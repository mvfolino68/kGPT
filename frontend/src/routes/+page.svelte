<script lang="ts">
	import { tick, onMount } from 'svelte';
	import { marked } from 'marked';
	import {
		chatMessages,
		currentSessionId,
		currentSession,
		sessions,
		sessionsLoading,
		isProcessing,
		loadSessions,
		startNewSession,
		loadSession,
		removeSession,
		renameSession,
		clearMessages,
		showAgentActivity,
		toggleAgentActivity,
		resetAgentTrace,
		handleAgentEvent,
		handleRoutingDecision,
		handleRetrievalResults,
		handleValidationResults,
		finalizeAgentTrace,
		type ChatMessage
	} from '$lib/stores/chat';
	import type { AgentEvent, RoutingDecision, RetrievalResults, ValidationResults } from '$lib/api';
	import { AgentActivitySidebar, RetroButton, StatusIndicator, RetroHeader, RetroCard } from '$lib/components';

	// State
	let inputValue = $state('');
	let messagesContainer: HTMLDivElement;
	let inputRef: HTMLTextAreaElement;
	let showHistory = $state(true);
	let editingSessionId = $state<string | null>(null);
	let editingTitle = $state('');
	let confirmingDeleteId = $state<string | null>(null);

	// Scroll to bottom of messages
	async function scrollToBottom() {
		await tick();
		if (messagesContainer) {
			messagesContainer.scrollTop = messagesContainer.scrollHeight;
		}
	}

	onMount(() => {
		loadSessions();
		inputRef?.focus();
	});

	// Extract text content safely from any value
	function extractTextContent(value: unknown): string {
		if (value === null || value === undefined) return '';
		if (typeof value === 'string') return value;
		if (typeof value === 'number') return String(value);
		if (Array.isArray(value)) {
			return value.map(item => {
				if (typeof item === 'string') return item;
				if (typeof item === 'object' && item !== null) {
					if ('text' in item && typeof item.text === 'string') return item.text;
					if ('content' in item && typeof item.content === 'string') return item.content;
				}
				return '';
			}).join('');
		}
		if (typeof value === 'object') {
			const obj = value as Record<string, unknown>;
			if ('text' in obj && typeof obj.text === 'string') return obj.text;
			if ('content' in obj && typeof obj.content === 'string') return obj.content;
		}
		return '';
	}

	// Send message
	async function sendMessage(message: string) {
		if (!message.trim() || $isProcessing) return;

		const userMessage = message.trim();
		inputValue = '';

		// Create session if needed
		let sessionId = $currentSessionId;
		if (!sessionId) {
			const title = userMessage.length > 40 ? userMessage.slice(0, 40) + '...' : userMessage;
			sessionId = await startNewSession(title);
		}

		// Add user message
		chatMessages.update(msgs => [...msgs, {
			id: crypto.randomUUID(),
			role: 'user',
			content: userMessage
		}]);
		await scrollToBottom();

		// Add assistant placeholder
		const assistantId = crypto.randomUUID();
		chatMessages.update(msgs => [...msgs, {
			id: assistantId,
			role: 'assistant',
			content: '',
			isStreaming: true,
			isThinking: true,
			thinkingStage: 'Analyzing...'
		}]);
		isProcessing.set(true);
		resetAgentTrace();
		await scrollToBottom();

		try {
			const history = $chatMessages
				.filter(m => m.id !== assistantId && m.role !== 'user' || m.content !== userMessage)
				.slice(0, -2)
				.map(m => ({ role: m.role, content: m.content }));

			const response = await fetch('/api/chat/stream', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					message: userMessage,
					history,
					session_id: sessionId
				})
			});

			if (!response.ok) throw new Error(`Request failed: ${response.statusText}`);
			if (!response.body) throw new Error('No response body');

			const reader = response.body.getReader();
			const decoder = new TextDecoder();
			let buffer = '';
			let fullContent = '';
			let hasStartedContent = false;

			while (true) {
				const { done, value } = await reader.read();
				if (done) break;

				buffer += decoder.decode(value, { stream: true });
				const lines = buffer.split('\n');
				buffer = lines.pop() || '';

				for (const line of lines) {
					if (!line.startsWith('data: ')) continue;
					const data = line.slice(6);
					if (data === '[DONE]') continue;

					try {
						const parsed = JSON.parse(data);

						// Handle stage updates
						if (parsed.stage !== undefined) {
							chatMessages.update(msgs => msgs.map(m =>
								m.id === assistantId ? { ...m, thinkingStage: parsed.stage } : m
							));
							continue;
						}

						// Handle agent events
						if (parsed.agent_event) {
							handleAgentEvent(parsed.agent_event as AgentEvent);
							continue;
						}

						// Handle routing decision
						if (parsed.routing_decision) {
							handleRoutingDecision(parsed.routing_decision as RoutingDecision);
							continue;
						}

						// Handle retrieval results
						if (parsed.retrieval_results) {
							handleRetrievalResults(parsed.retrieval_results as RetrievalResults);
							continue;
						}

						// Handle validation results
						if (parsed.validation_results) {
							handleValidationResults(parsed.validation_results as ValidationResults);
							continue;
						}

						// Handle actions
						if (parsed.actions) {
							chatMessages.update(msgs => msgs.map(m =>
								m.id === assistantId ? { ...m, actions: parsed.actions } : m
							));
							continue;
						}

						// Handle citations
						if (parsed.citations) {
							chatMessages.update(msgs => msgs.map(m =>
								m.id === assistantId ? { ...m, citations: parsed.citations } : m
							));
							continue;
						}

						// Handle cluster context
						if (parsed.cluster_context) {
							chatMessages.update(msgs => msgs.map(m =>
								m.id === assistantId ? { ...m, clusterContext: parsed.cluster_context } : m
							));
							continue;
						}

						// Handle admin result
						if (parsed.admin_result) {
							chatMessages.update(msgs => msgs.map(m =>
								m.id === assistantId ? { ...m, adminResult: parsed.admin_result } : m
							));
							continue;
						}

						// Handle content chunks
						const rawContent = parsed.choices?.[0]?.delta?.content;
						if (rawContent !== undefined && rawContent !== null) {
							const textContent = extractTextContent(rawContent);
							if (textContent) {
								if (!hasStartedContent) {
									hasStartedContent = true;
									chatMessages.update(msgs => msgs.map(m =>
										m.id === assistantId ? { ...m, isThinking: false } : m
									));
								}
								fullContent += textContent;
								chatMessages.update(msgs => msgs.map(m =>
									m.id === assistantId ? { ...m, content: fullContent } : m
								));
								await scrollToBottom();
							}
						}
					} catch {
						// Skip malformed JSON
					}
				}
			}

			// Finalize
			chatMessages.update(msgs => msgs.map(m =>
				m.id === assistantId ? { ...m, isStreaming: false, isThinking: false } : m
			));
			finalizeAgentTrace(assistantId);

		} catch (error) {
			chatMessages.update(msgs => msgs.map(m =>
				m.id === assistantId ? {
					...m,
					content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
					isStreaming: false,
					isThinking: false
				} : m
			));
		} finally {
			isProcessing.set(false);
			inputRef?.focus();
		}
	}

	// Handle keyboard input
	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault();
			sendMessage(inputValue);
		}
	}

	// Session management
	function handleNewChat() {
		clearMessages();
		inputRef?.focus();
	}

	async function handleSelectSession(sessionId: string) {
		if (sessionId === $currentSessionId) return;
		await loadSession(sessionId);
		await scrollToBottom();
	}

	function handleDeleteClick(sessionId: string, event: MouseEvent) {
		event.stopPropagation();
		confirmingDeleteId = sessionId;
	}

	async function handleConfirmDelete(sessionId: string, event: MouseEvent) {
		event.stopPropagation();
		await removeSession(sessionId);
		confirmingDeleteId = null;
	}

	function handleCancelDelete(event: MouseEvent) {
		event.stopPropagation();
		confirmingDeleteId = null;
	}

	function handleStartEdit(sessionId: string, title: string, event: MouseEvent) {
		event.stopPropagation();
		editingSessionId = sessionId;
		editingTitle = title;
	}

	async function handleSaveEdit() {
		if (editingSessionId && editingTitle.trim()) {
			await renameSession(editingSessionId, editingTitle.trim());
		}
		editingSessionId = null;
		editingTitle = '';
	}

	function handleEditKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter') handleSaveEdit();
		else if (event.key === 'Escape') {
			editingSessionId = null;
			editingTitle = '';
		}
	}

	// Render markdown safely
	function renderMarkdown(content: string): string {
		if (!content) return '';
		try {
			return marked.parse(content, { breaks: true, gfm: true }) as string;
		} catch {
			return content.replace(/\n/g, '<br>');
		}
	}

	// Format date
	function formatDate(dateStr: string): string {
		const date = new Date(dateStr);
		const now = new Date();
		const diff = now.getTime() - date.getTime();
		const days = Math.floor(diff / (1000 * 60 * 60 * 24));
		if (days === 0) return 'Today';
		if (days === 1) return 'Yesterday';
		if (days < 7) return `${days}d ago`;
		return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
	}

	// Extract domain from URL
	function extractDomain(url: string): string {
		try {
			return new URL(url).hostname.replace('www.', '');
		} catch {
			return url.split('/')[0] || url;
		}
	}

	// Quick actions
	const quickActions = [
		{ label: 'Cluster status', value: 'Show me my Kafka cluster status' },
		{ label: 'List topics', value: 'List all topics in my cluster' },
		{ label: 'Consumer lag', value: 'Show consumer group lag' },
		{ label: 'What can you do?', value: 'What admin operations can you perform?' }
	];
</script>

<svelte:head>
	<title>kGPT - Chat</title>
</svelte:head>

<div class="flex h-full bg-surface-950">
	<!-- History Sidebar -->
	{#if showHistory}
		<aside class="w-64 bg-surface-900/70 border-r retro-border flex flex-col backdrop-blur-sm">
			<div class="p-4 border-b retro-border flex items-center justify-between">
				<span class="text-xs font-bold font-mono text-surface-400 uppercase tracking-wider">Sessions</span>
				<RetroButton size="sm" variant="primary" onclick={handleNewChat}>
					<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
					</svg>
				</RetroButton>
			</div>

			<div class="flex-1 overflow-y-auto py-2 px-2">
				{#if $sessionsLoading}
					<div class="px-3 py-2 text-surface-500 text-xs font-mono">Loading...</div>
				{:else if $sessions.length === 0}
					<div class="px-3 py-2 text-surface-600 text-xs font-mono">No sessions yet</div>
				{:else}
					{#each $sessions as session (session.id)}
						<button
							onclick={() => handleSelectSession(session.id)}
							class="w-full group px-3 py-2.5 text-left rounded transition-all mb-1 font-mono
								{session.id === $currentSessionId ? 'retro-card-glow-green text-emerald-300' : 'retro-card hover:bg-surface-800/60 text-surface-300'}"
						>
							{#if editingSessionId === session.id}
								<input
									type="text"
									bind:value={editingTitle}
									onblur={handleSaveEdit}
									onkeydown={handleEditKeydown}
									class="w-full retro-input text-xs px-2 py-1"
								/>
							{:else}
								<div class="flex items-center justify-between">
									<span class="text-xs truncate flex-1">
										{session.id === $currentSessionId ? '> ' : ''}{session.title}
									</span>
									{#if confirmingDeleteId === session.id}
										<div class="flex gap-1">
											<RetroButton size="sm" variant="danger" onclick={(e) => handleConfirmDelete(session.id, e)}>
												DEL
											</RetroButton>
											<RetroButton size="sm" onclick={handleCancelDelete}>
												X
											</RetroButton>
										</div>
									{:else}
										<div class="flex gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
											<button onclick={(e) => handleStartEdit(session.id, session.title, e)} class="p-1 text-surface-500 hover:text-emerald-400 rounded">
												<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
													<path stroke-linecap="round" stroke-linejoin="round" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
												</svg>
											</button>
											<button onclick={(e) => handleDeleteClick(session.id, e)} class="p-1 text-surface-500 hover:text-red-400 rounded">
												<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
													<path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
												</svg>
											</button>
										</div>
									{/if}
								</div>
								<span class="text-[10px] text-surface-600 font-mono">{formatDate(session.updated_at)}</span>
							{/if}
						</button>
					{/each}
				{/if}
			</div>
		</aside>
	{/if}

	<!-- Main Chat Area -->
	<div class="flex-1 flex flex-col min-w-0">
		<!-- Header -->
		<RetroHeader path="kgpt/chat" flag={$currentSession ? `--session="${$currentSession.title}"` : ''}>
			{#snippet rightContent()}
				<RetroButton size="sm" onclick={() => showHistory = !showHistory}>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
						<path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16" />
					</svg>
				</RetroButton>
				{#if $chatMessages.length > 0}
					<RetroButton size="sm" onclick={handleNewChat}>
						+ New
					</RetroButton>
				{/if}
				<RetroButton size="sm" variant={$showAgentActivity ? 'primary' : 'default'} onclick={toggleAgentActivity}>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2z" />
					</svg>
				</RetroButton>
			{/snippet}
		</RetroHeader>

		<!-- Messages -->
		<div bind:this={messagesContainer} class="flex-1 overflow-y-auto p-6">
			<div class="max-w-4xl mx-auto space-y-6">
				{#if $chatMessages.length === 0}
					<!-- Empty State -->
					<RetroCard variant="glow-green" class="text-center py-12">
						<div class="w-20 h-20 rounded-xl retro-card-glow-green flex items-center justify-center mb-6 animate-glow-pulse mx-auto">
							<svg class="w-10 h-10 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
								<path stroke-linecap="round" stroke-linejoin="round" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
							</svg>
						</div>
						<h2 class="text-2xl font-bold font-mono text-surface-100 mb-2 text-glow-green">READY_</h2>
						<p class="text-surface-400 mb-8 max-w-md font-mono text-sm mx-auto">Query Kafka cluster, search docs, perform admin ops</p>

						<div class="flex flex-wrap justify-center gap-2">
							{#each quickActions as action}
								<RetroButton size="sm" onclick={() => sendMessage(action.value)}>
									{action.label}
								</RetroButton>
							{/each}
						</div>
					</RetroCard>
				{:else}
					<!-- Messages -->
					<div class="space-y-4">
						{#each $chatMessages as message (message.id)}
							{#if message.role === 'user'}
								<!-- User Message Card -->
								<div class="flex justify-end animate-slide-in-right">
									<RetroCard variant="glow-cyan" class="max-w-[75%] !p-0">
										<div class="px-4 py-3">
											<div class="flex items-center gap-2 mb-2">
												<span class="text-[10px] font-mono text-cyan-400 uppercase tracking-wider">User</span>
												<span class="text-[9px] font-mono text-surface-600">></span>
											</div>
											<p class="text-surface-100 text-sm leading-relaxed font-mono">{message.content}</p>
										</div>
									</RetroCard>
								</div>
							{:else}
								<!-- Assistant Message Card -->
								<div class="flex justify-start animate-slide-in-left">
									<div class="max-w-[80%] space-y-3">
										{#if message.isThinking && !message.content}
											<RetroCard class="!p-0">
												<div class="px-4 py-3 flex items-center gap-3">
													<div class="flex gap-1">
														<StatusIndicator status="active" pulse size="sm" />
														<StatusIndicator status="active" pulse size="sm" />
														<StatusIndicator status="active" pulse size="sm" />
													</div>
													<span class="text-sm font-mono text-surface-400">{message.thinkingStage || 'Processing...'}</span>
												</div>
											</RetroCard>
										{/if}

										{#if message.content}
											<RetroCard variant="glow-green" class="!p-0">
												<div class="px-4 py-3">
													<div class="flex items-center gap-2 mb-2">
														<span class="text-[10px] font-mono text-emerald-400 uppercase tracking-wider">kGPT</span>
														<StatusIndicator status="active" size="sm" />
													</div>
													<div class="prose prose-sm prose-invert max-w-none text-sm leading-relaxed">
														{@html renderMarkdown(message.content)}
													</div>
												</div>
											</RetroCard>
										{/if}

										<!-- Sources -->
										{#if message.citations && message.citations.length > 0 && !message.isStreaming}
											{@const uniqueDomains = [...new Set(message.citations.map(c => extractDomain(c)))]}
											<div class="flex items-center gap-2 px-2">
												<RetroCard class="!p-0 inline-flex">
													<div class="flex items-center gap-2 px-3 py-1.5">
														<svg class="w-3 h-3 text-surface-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
															<path stroke-linecap="round" stroke-linejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101" />
															<path stroke-linecap="round" stroke-linejoin="round" d="M10.172 13.828a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
														</svg>
														<span class="text-xs text-surface-400 font-mono">src:</span>
														{#each uniqueDomains.slice(0, 3) as domain}
															<span class="text-xs text-cyan-400 font-mono">{domain}</span>
														{/each}
														{#if uniqueDomains.length > 3}
															<span class="text-xs text-surface-500 font-mono">+{uniqueDomains.length - 3}</span>
														{/if}
													</div>
												</RetroCard>
											</div>
										{/if}

										<!-- Actions -->
										{#if message.actions && message.actions.length > 0 && !message.isStreaming}
											<div class="flex flex-wrap gap-2 px-2">
												{#each message.actions as action}
													<RetroButton size="sm" onclick={() => sendMessage(action.value)}>
														{action.label}
													</RetroButton>
												{/each}
											</div>
										{/if}
									</div>
								</div>
							{/if}
						{/each}
					</div>
				{/if}
			</div>
		</div>

		<!-- Input -->
		<div class="border-t retro-border bg-surface-900/60 backdrop-blur-sm p-6">
			<div class="max-w-4xl mx-auto space-y-2">
				<RetroCard variant="elevated" class="!p-0">
					<div class="flex items-end gap-3 p-3 focus-within:border-glow-green">
						<span class="text-emerald-400 font-mono text-lg pb-1">></span>
						<textarea
							bind:this={inputRef}
							bind:value={inputValue}
							onkeydown={handleKeydown}
							placeholder="Enter command..."
							disabled={$isProcessing}
							rows="1"
							class="flex-1 bg-transparent text-surface-100 placeholder-surface-600 resize-none focus:outline-none disabled:opacity-50 text-sm font-mono"
							style="field-sizing: content; max-height: 150px;"
						></textarea>
						<RetroButton
							variant="primary"
							size="sm"
							onclick={() => sendMessage(inputValue)}
							disabled={$isProcessing || !inputValue.trim()}
						>
							{#if $isProcessing}
								<svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
									<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
									<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
								</svg>
							{:else}
								<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
									<path stroke-linecap="round" stroke-linejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
								</svg>
							{/if}
						</RetroButton>
					</div>
				</RetroCard>
				<p class="text-center text-xs text-surface-600 font-mono">
					[ENTER] send | [SHIFT+ENTER] newline
				</p>
			</div>
		</div>
	</div>

	<!-- Agent Activity Sidebar -->
	<AgentActivitySidebar />
</div>

<style>
	.prose :global(p) {
		margin: 0.5rem 0;
		color: rgb(var(--color-surface-200));
	}
	.prose :global(p:first-child) {
		margin-top: 0;
	}
	.prose :global(p:last-child) {
		margin-bottom: 0;
	}
	.prose :global(ul), .prose :global(ol) {
		margin: 0.5rem 0;
		padding-left: 1.5rem;
	}
	.prose :global(li) {
		margin: 0.25rem 0;
	}
	.prose :global(code) {
		background: rgba(var(--color-surface-800), 0.8);
		padding: 0.125rem 0.375rem;
		border-radius: 0.25rem;
		font-size: 0.875em;
		color: rgb(var(--retro-green));
		border: 1px solid rgba(var(--retro-green), 0.2);
	}
	.prose :global(pre) {
		background: rgb(var(--color-surface-900));
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 0.5rem;
		padding: 1rem;
		overflow-x: auto;
		margin: 0.75rem 0;
	}
	.prose :global(pre code) {
		background: transparent;
		padding: 0;
		border: none;
	}
	.prose :global(h1), .prose :global(h2), .prose :global(h3) {
		margin-top: 1rem;
		margin-bottom: 0.5rem;
		font-weight: 600;
		color: rgb(var(--retro-green));
	}
	.prose :global(a) {
		color: rgb(var(--retro-cyan));
		text-decoration: underline;
	}
	.prose :global(blockquote) {
		border-left: 3px solid rgba(var(--retro-green), 0.3);
		padding-left: 1rem;
		margin: 0.75rem 0;
		color: rgb(var(--color-surface-400));
	}
</style>
