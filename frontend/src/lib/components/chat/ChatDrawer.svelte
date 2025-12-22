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
	import ChatEmptyState from './ChatEmptyState.svelte';
	import ChatInput from './ChatInput.svelte';
	import ChatHistory from './ChatHistory.svelte';
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

	function handleChatAction(event: string | CustomEvent<{ message: string }>) {
		const message = typeof event === 'string' ? event : event.detail.message;
		currentView = 'chat';
		inputValue = message;
		sendMessage(message);
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
					const citations = Array.isArray(event.data) ? event.data : (event.data?.citations || []);
					console.log('[kGPT DEBUG] Received citations:', citations);
					chatMessages.update(msgs => msgs.map(m => m.id === assistantId ? { ...m, citations } : m));
				} else if (event.type === 'actions') {
					// Ensure we have an array for actions too
					const actions = Array.isArray(event.data) ? event.data : (event.data?.actions || []);
					chatMessages.update(msgs => msgs.map(m => m.id === assistantId ? { ...m, actions } : m));
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
		if (event.key === 'Escape') {
			onClose();
		}
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
						class="px-3"
						onclick={() => currentView = 'chat'}
					>
						Chat
					</Button>
					<Button
						variant={currentView === 'history' ? 'secondary' : 'ghost'}
						size="sm"
						class="px-3"
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
					<ChatEmptyState onAction={handleChatAction} />
				{:else}
					{#each $chatMessages as message (message.id)}
						<ChatMessage {message} onActionClick={sendMessage} />
					{/each}
				{/if}
			</div>

			<!-- Input -->
			<ChatInput
				bind:value={inputValue}
				isProcessing={$isProcessing}
				onSend={sendMessage}
				onKeydown={handleKeydown}
			/>
		{:else}
			<!-- History View -->
			<ChatHistory
				sessions={$sessions}
				currentSessionId={$currentSessionId}
				sessionsLoading={$sessionsLoading}
				onSelect={handleSelectSession}
				onDelete={handleDeleteSession}
				onNewChat={handleNewChat}
			/>
		{/if}
	</div>

	<!-- Trace Panel - Side by side -->
	{#if showTrace}
		<AgentTracePanel onClose={() => showTrace = false} />
	{/if}
</div>
