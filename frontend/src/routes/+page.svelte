<script lang="ts">
	import { tick, onMount, onDestroy } from 'svelte';
	import { replaceState } from '$app/navigation';
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
		handleWebSearchResults,
		finalizeAgentTrace,
		selectMessageForTrace
	} from '$lib/stores/chat';
	import type { AgentEvent, RoutingDecision, RetrievalResults, ValidationResults, WebSearchResults } from '$lib/api';
	import {
		AgentActivitySidebar,
		RetroButton,
		RetroHeader,
		ChatHistory,
		ChatMessage,
		ChatInput,
		ChatEmptyState
	} from '$lib/components';
	import { processSSEStream, fetchWithAbort } from '$lib/utils/chat-stream';

	// State
	let inputValue = $state('');
	let messagesContainer: HTMLDivElement;
	let inputRef: any;
	let showHistory = $state(true);
	let editingSessionId = $state<string | null>(null);
	let editingTitle = $state('');
	let confirmingDeleteId = $state<string | null>(null);
	let currentAbort: (() => void) | null = null;

	// Scroll to bottom of messages
	async function scrollToBottom() {
		await tick();
		if (messagesContainer) {
			messagesContainer.scrollTop = messagesContainer.scrollHeight;
		}
	}

	onMount(async () => {
		await loadSessions();

		// Check URL for session ID on initial load
		const urlParams = new URLSearchParams(window.location.search);
		const sessionIdFromUrl = urlParams.get('session');
		if (sessionIdFromUrl) {
			try {
				await loadSession(sessionIdFromUrl);
				await scrollToBottom();
			} catch (error) {
				console.error('Failed to load session from URL:', error);
				// Clear invalid session from URL
				updateUrlWithSession(null);
			}
		}

		inputRef?.focus();
	});

	// Update browser URL with session ID
	function updateUrlWithSession(sessionId: string | null) {
		const url = new URL(window.location.href);
		if (sessionId) {
			url.searchParams.set('session', sessionId);
		} else {
			url.searchParams.delete('session');
		}
		replaceState(url, {});
	}

	onDestroy(() => {
		// Cancel any in-progress stream when leaving the page
		if (currentAbort) {
			currentAbort();
			currentAbort = null;
		}
	});

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
			updateUrlWithSession(sessionId);
		}

		// Add user message
		chatMessages.update(msgs => [
			...msgs,
			{
				id: crypto.randomUUID(),
				role: 'user',
				content: userMessage
			}
		]);
		await scrollToBottom();

		// Add assistant placeholder
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
		selectMessageForTrace(null); // Clear any selection when starting new message
		showAgentActivity.set(true); // Auto-open agent pipeline on new messages
		await scrollToBottom();

		try {
			const history = $chatMessages
				.filter(m => m.id !== assistantId && m.role !== 'user' || m.content !== userMessage)
				.slice(0, -2)
				.map(m => ({ role: m.role, content: m.content }));

			// Use fetchWithAbort to allow cancellation
			const { response, abort } = await fetchWithAbort(
				'/api/chat/stream',
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({
						message: userMessage,
						history,
						session_id: sessionId
					})
				},
				120000 // 2 minute timeout
			);
			currentAbort = abort;

			if (!response.ok) throw new Error(`Request failed: ${response.statusText}`);

			let fullContent = '';
			let hasStartedContent = false;

			for await (const event of processSSEStream(
				response,
				(stage) => {
					chatMessages.update(msgs =>
						msgs.map(m => (m.id === assistantId ? {
							...m,
							thinkingStage: stage,
							// Empty stage means done thinking (for admin ops with no content)
							isThinking: stage !== '' ? m.isThinking : false
						} : m))
					);
				},
				(agentEvent) => handleAgentEvent(agentEvent as AgentEvent),
				(decision) => handleRoutingDecision(decision as RoutingDecision),
				(results) => handleRetrievalResults(results as RetrievalResults),
				(results) => handleValidationResults(results as ValidationResults),
				// Web search results are now unified with citations, just update sidebar
				(results) => handleWebSearchResults(results as WebSearchResults),
				(context) => {
					chatMessages.update(msgs =>
						msgs.map(m => (m.id === assistantId ? { ...m, clusterContext: context } : m))
					);
				},
				(result) => {
					chatMessages.update(msgs =>
						msgs.map(m => (m.id === assistantId ? { ...m, adminResult: result } : m))
					);
				},
				(title) => {
					// Update session title when smart name is generated
					// Backend already updated the database, just update local store
					if (sessionId) {
						sessions.update((s) =>
							s.map((session) => (session.id === sessionId ? { ...session, title } : session))
						);
						currentSession.update((s) => (s?.id === sessionId ? { ...s, title } : s));
					}
				}
			)) {
				if (event.type === 'content') {
					if (!hasStartedContent) {
						hasStartedContent = true;
						chatMessages.update(msgs =>
							msgs.map(m => (m.id === assistantId ? { ...m, isThinking: false } : m))
						);
					}
					fullContent += event.data;
					chatMessages.update(msgs =>
						msgs.map(m => (m.id === assistantId ? { ...m, content: fullContent } : m))
					);
					await scrollToBottom();
				} else if (event.type === 'citations') {
					chatMessages.update(msgs =>
						msgs.map(m => (m.id === assistantId ? { ...m, citations: event.data } : m))
					);
				} else if (event.type === 'actions') {
					chatMessages.update(msgs =>
						msgs.map(m => (m.id === assistantId ? { ...m, actions: event.data } : m))
					);
				}
			}

			// Finalize
			chatMessages.update(msgs =>
				msgs.map(m => (m.id === assistantId ? { ...m, isStreaming: false, isThinking: false } : m))
			);
			finalizeAgentTrace(assistantId);
		} catch (error) {
			chatMessages.update(msgs =>
				msgs.map(m =>
					m.id === assistantId
						? {
								...m,
								content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
								isStreaming: false,
								isThinking: false
						  }
						: m
				)
			);
		} finally {
			// Clean up abort controller
			if (currentAbort) {
				currentAbort();
				currentAbort = null;
			}
			isProcessing.set(false);
			inputRef?.focus();
		}
	}

	// Session management
	function handleNewChat() {
		// Cancel any in-progress stream
		if (currentAbort) {
			currentAbort();
			currentAbort = null;
		}
		isProcessing.set(false);
		clearMessages();
		updateUrlWithSession(null);
		inputRef?.focus();
	}

	async function handleSelectSession(sessionId: string) {
		if (sessionId === $currentSessionId) return;
		await loadSession(sessionId);
		updateUrlWithSession(sessionId);
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
</script>

<svelte:head>
	<title>kGPT - Chat</title>
</svelte:head>

<div class="flex h-full bg-surface-950">
	<!-- History Sidebar -->
	{#if showHistory}
		<ChatHistory
			sessions={$sessions}
			sessionsLoading={$sessionsLoading}
			currentSessionId={$currentSessionId}
			editingSessionId={editingSessionId}
			bind:editingTitle
			confirmingDeleteId={confirmingDeleteId}
			onNewChat={handleNewChat}
			onSelectSession={handleSelectSession}
			onStartEdit={handleStartEdit}
			onSaveEdit={handleSaveEdit}
			onEditKeydown={handleEditKeydown}
			onEditInput={(val) => (editingTitle = val)}
			onDeleteClick={handleDeleteClick}
			onConfirmDelete={handleConfirmDelete}
			onCancelDelete={handleCancelDelete}
		/>
	{/if}

	<!-- Main Chat Area -->
	<div class="flex-1 flex flex-col min-w-0">
		<!-- Header -->
		<RetroHeader
			path="kgpt/chat"
			flag={$currentSession ? `--session="${$currentSession.title}"` : ''}
		>
			{#snippet rightContent()}
				<RetroButton size="sm" onclick={() => (showHistory = !showHistory)}>
					<svg
						class="w-4 h-4"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
						stroke-width="1.5"
					>
						<path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16" />
					</svg>
				</RetroButton>
				{#if $chatMessages.length > 0}
					<RetroButton size="sm" onclick={handleNewChat}> + New </RetroButton>
				{/if}
				<RetroButton
					size="sm"
					variant={$showAgentActivity ? 'primary' : 'default'}
					onclick={toggleAgentActivity}
				>
					<svg
						class="w-4 h-4"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
						stroke-width="2"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"
						/>
					</svg>
				</RetroButton>
			{/snippet}
		</RetroHeader>

		<!-- Messages -->
		<div bind:this={messagesContainer} class="flex-1 overflow-y-auto p-6">
			<div class="max-w-4xl mx-auto space-y-6">
				{#if $chatMessages.length === 0}
					<ChatEmptyState onQuickAction={sendMessage} />
				{:else}
					<div class="space-y-4">
						{#each $chatMessages as message (message.id)}
							<ChatMessage {message} onActionClick={sendMessage} />
						{/each}
					</div>
				{/if}
			</div>
		</div>

		<!-- Input -->
		<ChatInput
			bind:this={inputRef}
			bind:value={inputValue}
			disabled={$isProcessing}
			onSend={() => sendMessage(inputValue)}
			onInput={(val) => (inputValue = val)}
		/>
	</div>

	<!-- Agent Activity Sidebar -->
	<AgentActivitySidebar />
</div>
