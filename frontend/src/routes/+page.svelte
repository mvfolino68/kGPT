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
		addMessage,
		updateMessage,
		appendToMessage,
		setThinkingStage,
		clearMessages,
		type ChatMessage
	} from '$lib/stores/chat';
	import type { SuggestedAction } from '$lib/api';

	let inputValue = $state('');
	let messagesContainer: HTMLDivElement;
	let showHistory = $state(true);
	let editingSessionId = $state<string | null>(null);
	let editingTitle = $state('');
	let inputRef: HTMLTextAreaElement;

	// Configure marked for clean output
	marked.setOptions({
		breaks: true,
		gfm: true
	});

	function renderMarkdown(content: string): string {
		try {
			// Clean up excessive formatting that agents sometimes add
			let cleaned = content
				// Remove "Analysis:", "Answer:", etc. headers that are redundant
				.replace(/^(Analysis|Answer|Response):\s*/gim, '')
				// Clean up multiple consecutive newlines
				.replace(/\n{3,}/g, '\n\n');

			return marked.parse(cleaned) as string;
		} catch {
			return content.replace(/\n/g, '<br>');
		}
	}

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

	async function sendMessage(message: string, isAction = false) {
		if (!message.trim() || $isProcessing) return;

		const userMessage = message.trim();
		inputValue = '';

		// Create a new session if we don't have one
		let sessionId = $currentSessionId;
		if (!sessionId) {
			const title = userMessage.length > 40 ? userMessage.slice(0, 40) + '...' : userMessage;
			sessionId = await startNewSession(title);
		}

		// Add user message to local state
		addMessage({ role: 'user', content: userMessage });
		await scrollToBottom();

		// Add placeholder for assistant with thinking state
		const assistantId = addMessage({
			role: 'assistant',
			content: '',
			isStreaming: true,
			isThinking: true,
			thinkingStage: 'Analyzing query...'
		});
		isProcessing.set(true);
		await scrollToBottom();

		try {
			const history = $chatMessages
				.filter((m) => m.id !== assistantId)
				.map((m) => ({ role: m.role, content: m.content }));

			const response = await fetch('/api/chat/stream', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					message: userMessage,
					history: history.slice(0, -1),
					session_id: sessionId
				})
			});

			if (!response.ok) throw new Error(`Request failed: ${response.statusText}`);
			if (!response.body) throw new Error('No response body');

			const reader = response.body.getReader();
			const decoder = new TextDecoder();
			let buffer = '';
			let hasStartedContent = false;

			while (true) {
				const { done, value } = await reader.read();
				if (done) break;

				buffer += decoder.decode(value, { stream: true });
				const lines = buffer.split('\n');
				buffer = lines.pop() || '';

				for (const line of lines) {
					if (line.startsWith('data: ')) {
						const data = line.slice(6);
						if (data === '[DONE]') continue;

						try {
							const parsed = JSON.parse(data);

							// Handle thinking/stage updates
							if (parsed.stage) {
								setThinkingStage(assistantId, parsed.stage);
								continue;
							}

							// Handle suggested actions
							if (parsed.actions) {
								updateMessage(assistantId, { actions: parsed.actions });
								continue;
							}

							// Handle cluster context
							if (parsed.cluster_context) {
								updateMessage(assistantId, { clusterContext: parsed.cluster_context });
								continue;
							}

							// Handle regular content
							const content = parsed.choices?.[0]?.delta?.content;
							if (content) {
								if (!hasStartedContent) {
									hasStartedContent = true;
									updateMessage(assistantId, { isThinking: false });
								}
								appendToMessage(assistantId, content);
								await scrollToBottom();
							}
						} catch {
							// Skip malformed JSON
						}
					}
				}
			}

			// Mark as done
			updateMessage(assistantId, { isStreaming: false, isThinking: false });
		} catch (error) {
			updateMessage(assistantId, {
				content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
				isStreaming: false,
				isThinking: false
			});
		} finally {
			isProcessing.set(false);
			inputRef?.focus();
		}
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault();
			sendMessage(inputValue);
		}
	}

	function handleNewChat() {
		clearMessages();
		inputRef?.focus();
	}

	async function handleSelectSession(sessionId: string) {
		if (sessionId === $currentSessionId) return;
		await loadSession(sessionId);
		await scrollToBottom();
	}

	async function handleDeleteSession(sessionId: string, event: MouseEvent) {
		event.stopPropagation();
		if (confirm('Delete this chat?')) {
			await removeSession(sessionId);
		}
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
		if (event.key === 'Enter') {
			handleSaveEdit();
		} else if (event.key === 'Escape') {
			editingSessionId = null;
			editingTitle = '';
		}
	}

	function handleAction(action: SuggestedAction) {
		if (action.type === 'query') {
			sendMessage(action.value, true);
		} else if (action.type === 'navigate') {
			window.location.href = action.value;
		} else if (action.type === 'operation') {
			sendMessage(action.value, true);
		}
	}

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

	// Smart suggested queries based on context
	const quickActions: SuggestedAction[] = [
		{
			id: 'cluster-status',
			label: 'Check cluster status',
			type: 'query',
			value: 'Show me my Kafka cluster status',
			icon: '📊'
		},
		{
			id: 'list-topics',
			label: 'List topics',
			type: 'query',
			value: 'List all topics in my cluster',
			icon: '📋'
		},
		{
			id: 'consumer-lag',
			label: 'Consumer lag',
			type: 'query',
			value: 'Show consumer group lag',
			icon: '⏱️'
		},
		{
			id: 'producer-help',
			label: 'Producer setup',
			type: 'query',
			value: 'How do I configure a Kafka producer?',
			icon: '📤'
		}
	];
</script>

<svelte:head>
	<title>kGPT - Chat</title>
</svelte:head>

<div class="flex h-full bg-surface-950">
	<!-- Compact History Sidebar -->
	{#if showHistory}
		<aside class="w-56 bg-surface-900 border-r border-surface-800 flex flex-col">
			<div class="p-3 border-b border-surface-800 flex items-center justify-between">
				<span class="text-xs font-medium text-surface-400 uppercase tracking-wider">History</span>
				<button
					type="button"
					onclick={handleNewChat}
					class="w-6 h-6 flex items-center justify-center text-emerald-400 hover:bg-emerald-400/10 rounded transition-colors"
					title="New chat"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
					</svg>
				</button>
			</div>

			<div class="flex-1 overflow-y-auto">
				{#if $sessionsLoading}
					<div class="px-3 py-4 text-surface-500 text-xs">Loading...</div>
				{:else if $sessions.length === 0}
					<div class="px-3 py-4 text-surface-600 text-xs">No conversations yet</div>
				{:else}
					{#each $sessions as session (session.id)}
						<div
							role="button"
							tabindex="0"
							onclick={() => handleSelectSession(session.id)}
							onkeydown={(e) => e.key === 'Enter' && handleSelectSession(session.id)}
							class="group px-3 py-2.5 cursor-pointer transition-all border-l-2
								{session.id === $currentSessionId
								? 'bg-surface-800/80 border-emerald-400'
								: 'border-transparent hover:bg-surface-800/40 hover:border-surface-600'}"
						>
							{#if editingSessionId === session.id}
								<input
									type="text"
									bind:value={editingTitle}
									onblur={handleSaveEdit}
									onkeydown={handleEditKeydown}
									class="w-full bg-surface-800 border border-surface-600 rounded px-2 py-1 text-xs text-surface-100 focus:outline-none focus:border-emerald-400"
								/>
							{:else}
								<div class="flex items-center justify-between">
									<span class="text-sm text-surface-200 truncate flex-1 mr-2">
										{session.title}
									</span>
									<div class="flex gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
										<button
											type="button"
											onclick={(e) => handleStartEdit(session.id, session.title, e)}
											class="p-1 text-surface-500 hover:text-surface-300 rounded"
											aria-label="Rename chat"
										>
											<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
											</svg>
										</button>
										<button
											type="button"
											onclick={(e) => handleDeleteSession(session.id, e)}
											class="p-1 text-surface-500 hover:text-red-400 rounded"
											aria-label="Delete chat"
										>
											<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
											</svg>
										</button>
									</div>
								</div>
								<span class="text-xs text-surface-600">{formatDate(session.updated_at)}</span>
							{/if}
						</div>
					{/each}
				{/if}
			</div>
		</aside>
	{/if}

	<!-- Main Chat Area -->
	<div class="flex-1 flex flex-col">
		<!-- Minimal Header -->
		<header class="px-4 py-3 border-b border-surface-800 bg-surface-900/50 backdrop-blur-sm">
			<div class="flex items-center gap-3 max-w-4xl mx-auto">
				<button
					type="button"
					onclick={() => (showHistory = !showHistory)}
					class="text-surface-500 hover:text-surface-300 transition-colors"
					aria-label={showHistory ? 'Hide history' : 'Show history'}
				>
					<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
					</svg>
				</button>
				<div class="flex items-center gap-2">
					<span class="text-lg font-semibold text-surface-100">kGPT</span>
					{#if $currentSession}
						<span class="text-surface-600">•</span>
						<span class="text-sm text-surface-400 truncate max-w-[300px]">{$currentSession.title}</span>
					{/if}
				</div>
				{#if $chatMessages.length > 0}
					<button
						type="button"
						onclick={handleNewChat}
						class="ml-auto text-xs text-surface-500 hover:text-emerald-400 transition-colors flex items-center gap-1"
					>
						<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
						</svg>
						New
					</button>
				{/if}
			</div>
		</header>

		<!-- Messages area -->
		<div bind:this={messagesContainer} class="flex-1 overflow-y-auto">
			<div class="max-w-4xl mx-auto px-4 py-6">
				{#if $chatMessages.length === 0}
					<!-- Clean Empty State -->
					<div class="flex flex-col items-center justify-center min-h-[60vh] text-center">
						<div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-500/20 to-blue-500/20 flex items-center justify-center mb-6">
							<svg class="w-8 h-8 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
							</svg>
						</div>
						<h2 class="text-2xl font-semibold text-surface-100 mb-2">Ask me anything</h2>
						<p class="text-surface-400 mb-8 max-w-md">
							Query your Kafka cluster, search documentation, or get help with configurations.
						</p>

						<!-- Quick Actions Grid -->
						<div class="grid grid-cols-2 gap-2 w-full max-w-lg">
							{#each quickActions as action}
								<button
									type="button"
									onclick={() => handleAction(action)}
									class="flex items-center gap-3 p-3 text-left bg-surface-900 hover:bg-surface-800 border border-surface-800 hover:border-surface-700 rounded-lg transition-all group"
								>
									<span class="text-lg">{action.icon}</span>
									<span class="text-sm text-surface-300 group-hover:text-surface-100">{action.label}</span>
								</button>
							{/each}
						</div>
					</div>
				{:else}
					<!-- Messages -->
					<div class="space-y-6">
						{#each $chatMessages as message (message.id)}
							{#if message.role === 'user'}
								<!-- User Message - Clean & Minimal -->
								<div class="flex justify-end">
									<div class="max-w-[85%] bg-emerald-600/20 border border-emerald-500/30 rounded-2xl rounded-br-md px-4 py-3">
										<p class="text-surface-100">{message.content}</p>
									</div>
								</div>
							{:else}
								<!-- Assistant Message -->
								<div class="space-y-3">
									<!-- Thinking State -->
									{#if message.isThinking && !message.content}
										<div class="flex items-center gap-3 text-surface-400">
											<div class="flex gap-1">
												<span class="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style="animation-delay: 0ms"></span>
												<span class="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style="animation-delay: 150ms"></span>
												<span class="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style="animation-delay: 300ms"></span>
											</div>
											<span class="text-sm">{message.thinkingStage || 'Thinking...'}</span>
										</div>
									{/if}

									<!-- Response Content -->
									{#if message.content}
										<div class="prose prose-sm max-w-none
											prose-invert
											prose-headings:text-surface-100 prose-headings:font-semibold prose-headings:mb-2 prose-headings:mt-4
											prose-p:text-surface-200 prose-p:leading-relaxed prose-p:my-2
											prose-strong:text-surface-100 prose-strong:font-semibold
											prose-code:text-emerald-400 prose-code:bg-surface-800 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-sm prose-code:before:content-none prose-code:after:content-none
											prose-pre:bg-surface-900 prose-pre:border prose-pre:border-surface-700 prose-pre:rounded-lg
											prose-a:text-blue-400 prose-a:no-underline hover:prose-a:underline
											prose-li:text-surface-200 prose-li:my-1
											prose-ul:my-2 prose-ol:my-2
											prose-hr:border-surface-700">
											{@html renderMarkdown(message.content)}
										</div>
									{/if}

									<!-- Cluster Context Card (if present) -->
									{#if message.clusterContext}
										{@const brokerCount = message.clusterContext.broker_count ?? (typeof message.clusterContext.brokers === 'number' ? message.clusterContext.brokers : Object.keys(message.clusterContext.brokers || {}).length)}
										{@const topicCount = message.clusterContext.topic_count ?? message.clusterContext.topics?.length ?? 0}
										{@const groupCount = message.clusterContext.consumer_groups?.length ?? 0}
										<div class="mt-4 p-4 bg-surface-900 border border-surface-700 rounded-lg">
											<div class="flex items-center gap-2 mb-3">
												<svg class="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2" />
												</svg>
												<span class="text-sm font-medium text-surface-200">Cluster</span>
												{#if message.clusterContext.cluster_id}
													<span class="text-xs text-surface-500 font-mono">{message.clusterContext.cluster_id.slice(0, 8)}...</span>
												{/if}
											</div>
											<div class="grid grid-cols-3 gap-4 text-sm">
												<div>
													<span class="text-surface-500 text-xs">Brokers</span>
													<p class="text-surface-100 font-mono text-lg">{brokerCount}</p>
												</div>
												<div>
													<span class="text-surface-500 text-xs">Topics</span>
													<p class="text-surface-100 font-mono text-lg">{topicCount}</p>
												</div>
												<div>
													<span class="text-surface-500 text-xs">Groups</span>
													<p class="text-surface-100 font-mono text-lg">{groupCount}</p>
												</div>
											</div>
										</div>
									{/if}

									<!-- Suggested Actions -->
									{#if message.actions && message.actions.length > 0 && !message.isStreaming}
										<div class="flex flex-wrap gap-2 mt-4">
											{#each message.actions as action}
												<button
													type="button"
													onclick={() => handleAction(action)}
													class="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm bg-surface-800 hover:bg-surface-700 border border-surface-700 hover:border-surface-600 rounded-full text-surface-300 hover:text-surface-100 transition-all"
												>
													{#if action.icon}
														<span>{action.icon}</span>
													{/if}
													{action.label}
													<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
														<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
													</svg>
												</button>
											{/each}
										</div>
									{/if}

									<!-- Citations (clean, collapsible) -->
									{#if message.citations && message.citations.length > 0 && !message.isStreaming}
										<details class="mt-4 group">
											<summary class="text-xs text-surface-500 cursor-pointer hover:text-surface-400 flex items-center gap-1">
												<svg class="w-3 h-3 transition-transform group-open:rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24">
													<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
												</svg>
												{message.citations.length} source{message.citations.length !== 1 ? 's' : ''}
											</summary>
											<div class="mt-2 pl-4 border-l border-surface-700 space-y-1">
												{#each message.citations as citation}
													<a
														href={citation}
														target="_blank"
														rel="noopener noreferrer"
														class="block text-xs text-blue-400 hover:text-blue-300 truncate"
													>
														{citation}
													</a>
												{/each}
											</div>
										</details>
									{/if}
								</div>
							{/if}
						{/each}
					</div>
				{/if}
			</div>
		</div>

		<!-- Input Area - Clean & Modern -->
		<div class="border-t border-surface-800 bg-surface-900/80 backdrop-blur-sm p-4">
			<div class="max-w-4xl mx-auto">
				<div class="relative flex items-end gap-3 bg-surface-800 border border-surface-700 rounded-xl p-2 focus-within:border-emerald-500/50 transition-colors">
					<textarea
						bind:this={inputRef}
						bind:value={inputValue}
						onkeydown={handleKeydown}
						placeholder="Ask about your cluster or documentation..."
						disabled={$isProcessing}
						rows="1"
						class="flex-1 bg-transparent text-surface-100 placeholder-surface-500 resize-none focus:outline-none disabled:opacity-50 px-2 py-1.5 max-h-32"
						style="field-sizing: content;"
					></textarea>
					<button
						type="button"
						onclick={() => sendMessage(inputValue)}
						disabled={$isProcessing || !inputValue.trim()}
						class="flex-shrink-0 w-9 h-9 flex items-center justify-center bg-emerald-600 hover:bg-emerald-500 disabled:bg-surface-700 disabled:text-surface-500 text-white rounded-lg transition-colors"
					>
						{#if $isProcessing}
							<svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
								<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
								<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
							</svg>
						{:else}
							<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
							</svg>
						{/if}
					</button>
				</div>
				<p class="text-center text-xs text-surface-600 mt-2">
					Press Enter to send • Shift+Enter for new line
				</p>
			</div>
		</div>
	</div>
</div>
