<script lang="ts">
	import { tick, onMount, onDestroy } from 'svelte';
	import { Button, Badge, Icon, IconButton, ListItem, Backdrop } from '$lib/components/ui';
	import {
		chatMessages,
		currentSessionId,
		sessions,
		sessionsLoading,
		isProcessing,
		loadSessions,
		startNewSession,
		loadSession,
		removeSession,
		clearMessages,
		resetAgentTrace,
		handleAgentEvent,
		handleRoutingDecision,
		handleRetrievalResults,
		handleValidationResults,
		handleWebSearchResults,
		finalizeAgentTrace,
		displayedAgentTrace,
		selectedMessageId,
		selectMessageForTrace
	} from '$lib/stores/chat';
	import type { AgentEvent, RoutingDecision, RetrievalResults, ValidationResults, WebSearchResults } from '$lib/stores/chat';
	import { processSSEStream, fetchWithAbort } from '$lib/utils/chat-stream';
	import ChatMessage from './ChatMessage.svelte';
	import AgentTracePanel from './AgentTracePanel.svelte';

	interface Props {
		onClose: () => void;
	}

	let { onClose }: Props = $props();

	// View state
	type View = 'chat' | 'history';
	let currentView = $state<View>('chat');
	let showTrace = $state(true); // Visible by default

	// Chat state
	let inputValue = $state('');
	let messagesContainer: HTMLDivElement | null = $state(null);
	let inputRef: HTMLTextAreaElement | null = $state(null);
	let currentAbort: (() => void) | null = null;

	// Derived
	let hasTrace = $derived($displayedAgentTrace.agentTimeline.length > 0 || $displayedAgentTrace.routingDecision !== null);

	// Auto-open trace panel when a message is selected via "View Trace" button
	$effect(() => {
		if ($selectedMessageId !== null) {
			showTrace = true;
		}
	});

	async function scrollToBottom() {
		await tick();
		if (messagesContainer) {
			messagesContainer.scrollTop = messagesContainer.scrollHeight;
		}
	}

	function handleChatAction(event: CustomEvent<{ message: string }>) {
		currentView = 'chat';
		inputValue = event.detail.message;
		sendMessage(event.detail.message);
	}

	onMount(async () => {
		await loadSessions();
		inputRef?.focus();
		window.addEventListener('chat-action', handleChatAction as EventListener);
	});

	onDestroy(() => {
		window.removeEventListener('chat-action', handleChatAction as EventListener);
		if (currentAbort) {
			currentAbort();
			currentAbort = null;
		}
	});

	async function sendMessage(message: string) {
		if (!message.trim() || $isProcessing) return;

		const userMessage = message.trim();
		inputValue = '';
		currentView = 'chat';

		let sessionId = $currentSessionId;
		if (!sessionId) {
			const title = userMessage.length > 40 ? userMessage.slice(0, 40) + '...' : userMessage;
			sessionId = await startNewSession(title);
		}

		chatMessages.update(msgs => [
			...msgs,
			{ id: crypto.randomUUID(), role: 'user', content: userMessage }
		]);
		await scrollToBottom();

		const assistantId = crypto.randomUUID();
		chatMessages.update(msgs => [
			...msgs,
			{
				id: assistantId,
				role: 'assistant',
				content: '',
				isStreaming: true,
				isThinking: true,
				thinkingStage: 'Analyzing...'
			}
		]);
		isProcessing.set(true);
		resetAgentTrace();
		await scrollToBottom();

		try {
			const history = $chatMessages
				.filter(m => m.id !== assistantId && m.role !== 'user' || m.content !== userMessage)
				.slice(0, -2)
				.map(m => ({ role: m.role, content: m.content }));

			const { response, abort } = await fetchWithAbort(
				'/api/chat/stream',
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({ message: userMessage, history, session_id: sessionId })
				},
				120000
			);
			currentAbort = abort;

			if (!response.ok) throw new Error(`Request failed: ${response.statusText}`);

			let fullContent = '';
			let hasStartedContent = false;

			for await (const event of processSSEStream(
				response,
				(stage) => {
					chatMessages.update(msgs =>
						msgs.map(m => m.id === assistantId ? { ...m, thinkingStage: stage, isThinking: stage !== '' ? m.isThinking : false } : m)
					);
				},
				(agentEvent) => handleAgentEvent(agentEvent as AgentEvent),
				(decision) => handleRoutingDecision(decision as RoutingDecision),
				(results) => handleRetrievalResults(results as RetrievalResults),
				(results) => handleValidationResults(results as ValidationResults),
				(results) => handleWebSearchResults(results as WebSearchResults),
				(context) => {
					chatMessages.update(msgs => msgs.map(m => m.id === assistantId ? { ...m, clusterContext: context } : m));
				},
				(result) => {
					chatMessages.update(msgs => msgs.map(m => m.id === assistantId ? { ...m, adminResult: result } : m));
				},
				() => {}
			)) {
				if (event.type === 'content') {
					if (!hasStartedContent) {
						hasStartedContent = true;
						chatMessages.update(msgs => msgs.map(m => m.id === assistantId ? { ...m, isThinking: false } : m));
					}
					fullContent += event.data;
					chatMessages.update(msgs => msgs.map(m => m.id === assistantId ? { ...m, content: fullContent } : m));
					await scrollToBottom();
				} else if (event.type === 'citations') {
					chatMessages.update(msgs => msgs.map(m => m.id === assistantId ? { ...m, citations: event.data } : m));
				} else if (event.type === 'actions') {
					chatMessages.update(msgs => msgs.map(m => m.id === assistantId ? { ...m, actions: event.data } : m));
				}
			}

			chatMessages.update(msgs => msgs.map(m => m.id === assistantId ? { ...m, isStreaming: false, isThinking: false } : m));
			finalizeAgentTrace(assistantId);
		} catch (error) {
			chatMessages.update(msgs =>
				msgs.map(m => m.id === assistantId
					? { ...m, content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`, isStreaming: false, isThinking: false }
					: m
				)
			);
		} finally {
			if (currentAbort) {
				currentAbort();
				currentAbort = null;
			}
			isProcessing.set(false);
			inputRef?.focus();
		}
	}

	function handleNewChat() {
		if (currentAbort) {
			currentAbort();
			currentAbort = null;
		}
		isProcessing.set(false);
		clearMessages();
		currentView = 'chat';
		inputRef?.focus();
	}

	async function handleSelectSession(sessionId: string) {
		await loadSession(sessionId);
		currentView = 'chat';
		await scrollToBottom();
	}

	async function handleDeleteSession(sessionId: string) {
		await removeSession(sessionId);
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault();
			sendMessage(inputValue);
		}
		if (event.key === 'Escape') {
			onClose();
		}
	}

	function formatDate(dateStr: string): string {
		const date = new Date(dateStr);
		const now = new Date();
		const diff = now.getTime() - date.getTime();
		const days = Math.floor(diff / (1000 * 60 * 60 * 24));

		if (days === 0) return 'Today';
		if (days === 1) return 'Yesterday';
		if (days < 7) return `${days} days ago`;
		return date.toLocaleDateString();
	}
</script>

<!-- Backdrop -->
<!-- Backdrop -->
<Backdrop onClose={onClose} />

<!-- Main Container - Side by side layout -->
<div class="fixed top-0 right-0 bottom-0 z-50 flex animate-slide-in-right shadow-2xl">
	<!-- Chat Panel -->
	<div class="w-[480px] bg-surface-900 flex flex-col">
		<!-- Header -->
		<header class="flex items-center justify-between px-4 py-3 bg-surface-800">
			<div class="flex items-center gap-2">
				<!-- View Toggle -->
				<div class="flex bg-surface-800 rounded-lg p-0.5 gap-0.5">
					<Button
						variant={currentView === 'chat' ? 'secondary' : 'ghost'}
						size="sm"
						class="rounded-md px-3"
						onclick={() => currentView = 'chat'}
					>
						Chat
					</Button>
					<Button
						variant={currentView === 'history' ? 'secondary' : 'ghost'}
						size="sm"
						class="rounded-md px-3"
						onclick={() => currentView = 'history'}
					>
						<span class="flex items-center gap-2">
							History
							{#if $sessions.length > 0}
								<span class="text-[10px] bg-surface-600 px-1.5 py-0.5 rounded">
									{$sessions.length}
								</span>
							{/if}
						</span>
					</Button>
				</div>
			</div>

			<div class="flex items-center gap-2">
				<!-- Toggle Trace Panel -->
				<Button
					variant={showTrace ? 'primary' : 'ghost'}
					size="sm"
					onclick={() => showTrace = !showTrace}
					title={showTrace ? 'Hide trace panel' : 'Show trace panel'}
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
						<path stroke-linecap="round" stroke-linejoin="round" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
					</svg>
					{#if $isProcessing}
						<span class="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse"></span>
					{/if}
				</Button>

				<!-- New Chat -->
				{#if $chatMessages.length > 0}
					<Button variant="ghost" size="sm" onclick={handleNewChat}>
						New
					</Button>
				{/if}

				<!-- Close -->
				<Button variant="ghost" size="icon" onclick={onClose}>
					<Icon name="close" size="md" />
				</Button>
			</div>
		</header>

		<!-- Content -->
		{#if currentView === 'chat'}
			<!-- Chat View -->
			<div bind:this={messagesContainer} class="flex-1 overflow-y-auto p-4 space-y-4">
				{#if $chatMessages.length === 0}
					<div class="flex flex-col items-center justify-center h-full text-center py-8">
						<div class="w-14 h-14 rounded-2xl bg-primary/10 flex items-center justify-center mb-4">
							<Icon name="sparkles" size="lg" class="text-primary-light" />
						</div>
						<h3 class="text-lg font-semibold text-surface-200 mb-2">How can I help?</h3>
						<p class="text-sm text-surface-500 max-w-xs mb-6">
							Ask me to manage topics, describe consumer groups, or help with Kafka configuration.
						</p>

						<div class="space-y-2 w-full max-w-xs">
							<Button
								variant="secondary"
								size="lg"
								class="w-full justify-start text-left bg-surface-800 hover:bg-surface-700/70 text-surface-300"
								onclick={() => sendMessage('List all topics')}
							>
								List all topics
							</Button>
							<Button
								variant="secondary"
								size="lg"
								class="w-full justify-start text-left bg-surface-800 hover:bg-surface-700/70 text-surface-300"
								onclick={() => sendMessage('Show consumer groups')}
							>
								Show consumer groups
							</Button>
							<Button
								variant="secondary"
								size="lg"
								class="w-full justify-start text-left bg-surface-800 hover:bg-surface-700/70 text-surface-300"
								onclick={() => sendMessage('How do I create a topic?')}
							>
								How do I create a topic?
							</Button>
						</div>
					</div>
				{:else}
					{#each $chatMessages as message (message.id)}
						<ChatMessage {message} onActionClick={sendMessage} />
					{/each}
				{/if}
			</div>

			<!-- Input -->
			<div class="p-4 bg-surface-800">
				<div class="flex items-end gap-2">
					<textarea
						bind:this={inputRef}
						bind:value={inputValue}
						onkeydown={handleKeydown}
						placeholder="Ask about your cluster..."
						disabled={$isProcessing}
						rows="1"
						class="flex-1 bg-surface-700/50 border-none rounded-md px-3 py-2 text-sm text-foreground placeholder:text-muted resize-none transition-all focus:outline-none focus:bg-surface-700 focus:ring-2 focus:ring-primary-600/50"
						style="field-sizing: content; max-height: 120px;"
					></textarea>
					<Button
						variant="primary"
						size="icon"
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
								<path stroke-linecap="round" stroke-linejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
							</svg>
						{/if}
					</Button>
				</div>
			</div>
		{:else}
			<!-- History View -->
			<div class="flex-1 overflow-y-auto">
				{#if $sessionsLoading}
					<div class="flex items-center justify-center py-12">
						<svg class="w-6 h-6 text-surface-500 animate-spin" fill="none" viewBox="0 0 24 24">
							<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
							<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
						</svg>
					</div>
				{:else if $sessions.length === 0}
					<div class="flex flex-col items-center justify-center h-full text-center py-8 px-4">
						<div class="w-14 h-14 rounded-2xl bg-surface-800 flex items-center justify-center mb-4">
							<svg class="w-7 h-7 text-surface-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
								<path stroke-linecap="round" stroke-linejoin="round" d="M20.25 8.511c.884.284 1.5 1.128 1.5 2.097v4.286c0 1.136-.847 2.1-1.98 2.193-.34.027-.68.052-1.02.072v3.091l-3-3c-1.354 0-2.694-.055-4.02-.163a2.115 2.115 0 01-.825-.242m9.345-8.334a2.126 2.126 0 00-.476-.095 48.64 48.64 0 00-8.048 0c-1.131.094-1.976 1.057-1.976 2.192v4.286c0 .837.46 1.58 1.155 1.951m9.345-8.334V6.637c0-1.621-1.152-3.026-2.76-3.235A48.455 48.455 0 0011.25 3c-2.115 0-4.198.137-6.24.402-1.608.209-2.76 1.614-2.76 3.235v6.226c0 1.621 1.152 3.026 2.76 3.235.577.075 1.157.14 1.74.194V21l4.155-4.155" />
							</svg>
						</div>
						<h3 class="text-lg font-semibold text-surface-300 mb-2">No Conversations</h3>
						<p class="text-sm text-surface-500 max-w-xs">
							Start a new chat to begin a conversation
						</p>
						<Button variant="primary" class="mt-4" onclick={handleNewChat}>
							Start New Chat
						</Button>
					</div>
				{:else}
					<div class="p-2 space-y-1">
						{#each $sessions as session (session.id)}
							{@const isActive = session.id === $currentSessionId}
							<div class="group flex items-center gap-1">
								<ListItem
									variant="subtle"
									active={isActive}
									class="flex-1 min-w-0 px-3 py-3 rounded-lg"
									onclick={() => handleSelectSession(session.id)}
								>
									<div class="flex items-center justify-between gap-2">
										<div class="min-w-0 flex-1">
											<p class="text-sm font-medium text-surface-200 truncate">{session.title}</p>
											<p class="text-xs text-surface-500 mt-0.5">{formatDate(session.updated_at)}</p>
										</div>
										{#if isActive}
											<Badge variant="primary" size="sm">Active</Badge>
										{/if}
									</div>
								</ListItem>
								<IconButton
									variant="danger"
									size="xs"
									class="mr-2 opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
									title="Delete session"
									onclick={(e) => { e.stopPropagation(); handleDeleteSession(session.id); }}
								>
									<Icon name="trash" size="sm" strokeWidth={2} />
								</IconButton>
							</div>
						{/each}
					</div>
				{/if}
			</div>
		{/if}
	</div>

	<!-- Trace Panel - Side by side -->
	{#if showTrace}
		<AgentTracePanel onClose={() => showTrace = false} />
	{/if}
</div>
