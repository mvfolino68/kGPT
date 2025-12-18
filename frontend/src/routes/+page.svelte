<script lang="ts">
	import { tick, onMount } from 'svelte';
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
	import type { SuggestedAction, AdminOperationResult } from '$lib/api';
	import { executeAdminOperation } from '$lib/api';
	import { FormattedMessage, MessageCard, MetricCard } from '$lib/components';

	let inputValue = $state('');
	let messagesContainer: HTMLDivElement;
	let showHistory = $state(true);
	let editingSessionId = $state<string | null>(null);
	let editingTitle = $state('');
	let inputRef: HTMLTextAreaElement;
	let confirmingDeleteId = $state<string | null>(null);
	let executingOperationId = $state<string | null>(null);

	// Admin operation form state
	let adminFormValues = $state<Record<string, string | number>>({});

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

		let sessionId = $currentSessionId;
		if (!sessionId) {
			const title = userMessage.length > 40 ? userMessage.slice(0, 40) + '...' : userMessage;
			sessionId = await startNewSession(title);
		}

		addMessage({ role: 'user', content: userMessage });
		await scrollToBottom();

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

							if (parsed.stage) {
								setThinkingStage(assistantId, parsed.stage);
								continue;
							}

							if (parsed.actions) {
								updateMessage(assistantId, { actions: parsed.actions });
								continue;
							}

							if (parsed.cluster_context) {
								updateMessage(assistantId, { clusterContext: parsed.cluster_context });
								continue;
							}

							if (parsed.admin_result) {
								updateMessage(assistantId, { adminResult: parsed.admin_result });
								continue;
							}

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
		if (event.key === 'Enter') {
			handleSaveEdit();
		} else if (event.key === 'Escape') {
			editingSessionId = null;
			editingTitle = '';
		}
	}

	function handleAction(action: { id: string; label: string; type: string; value: string }) {
		if (action.type === 'query' || action.type === 'operation') {
			sendMessage(action.value, true);
		} else if (action.type === 'navigate') {
			window.location.href = action.value;
		}
	}

	function handleSuggestedAction(action: SuggestedAction) {
		if (action.type === 'query' || action.type === 'operation') {
			sendMessage(action.value, true);
		} else if (action.type === 'navigate') {
			window.location.href = action.value;
		}
	}

	async function handleConfirmOperation(messageId: string, operation: string, params: Record<string, unknown>) {
		executingOperationId = messageId;
		try {
			const result = await executeAdminOperation({ operation, params });

			// Update the message with the execution result (remove pending, show actual result)
			updateMessage(messageId, {
				adminResult: {
					...result,
					pending: false // No longer pending
				}
			});
		} catch (error) {
			// Update with error
			updateMessage(messageId, {
				adminResult: {
					success: false,
					pending: false,
					operation,
					error: error instanceof Error ? error.message : 'Unknown error'
				}
			});
		} finally {
			executingOperationId = null;
		}
	}

	function handleCancelOperation(messageId: string) {
		// Update the message to show the operation was cancelled
		updateMessage(messageId, {
			adminResult: {
				success: false,
				pending: false,
				operation: 'cancelled',
				message: 'Operation cancelled by user'
			}
		});
	}

	function handleAdminFormSubmit(messageId: string, operation: string, existingParams: Record<string, unknown>) {
		// Merge form values with existing params
		const formData = { ...existingParams, ...adminFormValues };

		// If we have a valid operation and all required fields, execute directly
		if (operation && operation !== '') {
			// Validate required fields based on operation
			let hasAllRequiredFields = false;

			if (operation === 'create_topic') {
				hasAllRequiredFields = !!formData.topic_name;
			} else if (operation === 'delete_topic') {
				hasAllRequiredFields = !!formData.topic_name;
			} else if (operation === 'describe_topic') {
				hasAllRequiredFields = !!formData.topic_name;
			} else if (operation === 'add_partitions') {
				hasAllRequiredFields = !!formData.topic_name && !!formData.new_total_partitions;
			} else if (operation === 'alter_topic_config') {
				hasAllRequiredFields = !!formData.topic_name && !!formData.config_key && !!formData.config_value;
			} else if (operation === 'delete_consumer_group') {
				hasAllRequiredFields = !!formData.group_id;
			} else if (operation === 'describe_consumer_group') {
				hasAllRequiredFields = !!formData.group_id;
			}

			// If we have all required fields, execute directly
			if (hasAllRequiredFields) {
				// Clear form values
				adminFormValues = {};
				// Execute the operation directly
				handleConfirmOperation(messageId, operation, formData);
				return;
			}
		}

		// Otherwise, send a natural language message for re-analysis
		let message = '';

		if (operation === 'create_topic') {
			message = `Create a topic named "${formData.topic_name}"`;
			if (formData.num_partitions) message += ` with ${formData.num_partitions} partitions`;
			if (formData.replication_factor) message += ` and replication factor ${formData.replication_factor}`;
		} else if (operation === 'delete_topic') {
			message = `Delete the topic "${formData.topic_name}"`;
		} else if (operation === 'describe_topic') {
			message = `Describe the topic "${formData.topic_name}"`;
		} else if (operation === 'add_partitions') {
			message = `Add partitions to "${formData.topic_name}" to have ${formData.new_total_partitions} total`;
		} else if (operation === 'alter_topic_config') {
			message = `Change ${formData.config_key} to ${formData.config_value} for topic "${formData.topic_name}"`;
		} else if (operation === 'delete_consumer_group') {
			message = `Delete consumer group "${formData.group_id}"`;
		} else {
			// Generic fallback - include operation in message if available
			if (operation && operation !== '') {
				message = `Perform ${operation} operation with parameters: ${JSON.stringify(formData)}`;
			} else {
				message = `with parameters: ${JSON.stringify(formData)}`;
			}
		}

		// Clear form values
		adminFormValues = {};

		// Send the message
		sendMessage(message, true);
	}

	function handleSelectOperation(operationId: string) {
		// Send a message to initiate the specific operation
		const messages: Record<string, string> = {
			'create_topic': 'I want to create a new topic',
			'delete_topic': 'I want to delete a topic',
			'alter_topic_config': 'I want to change topic configuration',
			'add_partitions': 'I want to add partitions to a topic',
			'delete_consumer_group': 'I want to delete a consumer group'
		};
		sendMessage(messages[operationId] || `I want to perform ${operationId}`, true);
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

	// Query actions with icon types
	const queryActions = [
		{
			id: 'cluster-status',
			label: 'Check cluster status',
			type: 'query',
			value: 'Show me my Kafka cluster status',
			iconType: 'cluster',
			color: 'emerald'
		},
		{
			id: 'list-topics',
			label: 'List topics',
			type: 'query',
			value: 'List all topics in my cluster',
			iconType: 'topics',
			color: 'blue'
		},
		{
			id: 'consumer-lag',
			label: 'Consumer lag',
			type: 'query',
			value: 'Show consumer group lag',
			iconType: 'lag',
			color: 'amber'
		},
		{
			id: 'help',
			label: 'What can you do?',
			type: 'query',
			value: 'What admin operations can you perform on my Kafka cluster?',
			iconType: 'help',
			color: 'violet'
		}
	];

	// Admin operations - these now trigger guided conversations
	const adminActions = [
		{
			id: 'create-topic',
			label: 'Create topic',
			type: 'operation',
			value: 'I want to create a new topic',
			iconType: 'add',
			color: 'emerald'
		},
		{
			id: 'delete-topic',
			label: 'Delete topic',
			type: 'operation',
			value: 'I want to delete a topic',
			iconType: 'delete',
			color: 'red'
		},
		{
			id: 'alter-config',
			label: 'Alter topic config',
			type: 'operation',
			value: 'I want to change topic configuration',
			iconType: 'settings',
			color: 'blue'
		},
		{
			id: 'add-partitions',
			label: 'Add partitions',
			type: 'operation',
			value: 'I want to add partitions to a topic',
			iconType: 'partition',
			color: 'violet'
		}
	];
</script>

<svelte:head>
	<title>kGPT - Chat</title>
</svelte:head>

<div class="chat-page flex h-full bg-surface-950">
	<!-- History Sidebar -->
	{#if showHistory}
		<aside class="w-64 bg-surface-900/60 backdrop-blur-xl border-r border-white/5 flex flex-col">
			<div class="p-4 border-b border-white/5 flex items-center justify-between">
				<span class="text-[11px] font-semibold text-surface-500 uppercase tracking-[0.15em]">History</span>
				<button
					type="button"
					onclick={handleNewChat}
					class="w-8 h-8 flex items-center justify-center text-emerald-400 hover:bg-emerald-500/10 rounded-lg transition-all duration-200 hover:scale-105 active:scale-95"
					title="New chat"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
					</svg>
				</button>
			</div>

			<div class="flex-1 overflow-y-auto py-2 space-y-1">
				{#if $sessionsLoading}
					<div class="px-4 py-3 text-surface-500 text-xs font-mono animate-pulse">Loading...</div>
				{:else if $sessions.length === 0}
					<div class="px-4 py-3 text-surface-600 text-xs">No conversations yet</div>
				{:else}
					{#each $sessions as session (session.id)}
						<div
							role="button"
							tabindex="0"
							onclick={() => handleSelectSession(session.id)}
							onkeydown={(e) => e.key === 'Enter' && handleSelectSession(session.id)}
							class="group mx-2 px-3 py-2.5 cursor-pointer rounded-lg transition-all duration-200
								{session.id === $currentSessionId
								? 'bg-emerald-500/10 ring-1 ring-emerald-500/20'
								: 'hover:bg-white/5'}"
						>
							{#if editingSessionId === session.id}
								<input
									type="text"
									bind:value={editingTitle}
									onblur={handleSaveEdit}
									onkeydown={handleEditKeydown}
									class="w-full bg-surface-800 border border-surface-600 rounded-lg px-2.5 py-1.5 text-sm text-surface-100 focus:outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20"
								/>
							{:else}
								<div class="flex items-center justify-between gap-2">
									<span class="text-[13px] truncate flex-1 {session.id === $currentSessionId ? 'text-emerald-300 font-medium' : 'text-surface-300'}">
										{session.title}
									</span>
									{#if confirmingDeleteId === session.id}
										<div class="flex gap-1.5">
											<button
												type="button"
												onclick={(e) => handleConfirmDelete(session.id, e)}
												class="px-2 py-1 text-[10px] font-semibold bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-md transition-all flex items-center gap-1"
												aria-label="Confirm delete"
											>
												<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
													<path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
												</svg>
												Delete
											</button>
											<button
												type="button"
												onclick={handleCancelDelete}
												class="px-2 py-1 text-[10px] font-semibold bg-surface-700 hover:bg-surface-600 text-surface-300 rounded-md transition-all"
												aria-label="Cancel delete"
											>
												Cancel
											</button>
										</div>
									{:else}
										<div class="flex gap-0.5 opacity-0 group-hover:opacity-100 transition-all duration-200">
											<button
												type="button"
												onclick={(e) => handleStartEdit(session.id, session.title, e)}
												class="p-1.5 text-surface-500 hover:text-surface-300 hover:bg-white/10 rounded-md transition-all"
												aria-label="Rename chat"
											>
												<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
													<path stroke-linecap="round" stroke-linejoin="round" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
												</svg>
											</button>
											<button
												type="button"
												onclick={(e) => handleDeleteClick(session.id, e)}
												class="p-1.5 text-surface-500 hover:text-red-400 hover:bg-red-500/10 rounded-md transition-all"
												aria-label="Delete chat"
											>
												<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
													<path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
												</svg>
											</button>
										</div>
									{/if}
								</div>
								<span class="text-[10px] text-surface-600 font-mono mt-0.5 block">{formatDate(session.updated_at)}</span>
							{/if}
						</div>
					{/each}
				{/if}
			</div>
		</aside>
	{/if}

	<!-- Main Chat Area -->
	<div class="flex-1 flex flex-col min-w-0">
		<!-- Header -->
		<header class="px-4 py-3 border-b border-white/5 bg-surface-900/40 backdrop-blur-xl">
			<div class="flex items-center gap-3 max-w-4xl mx-auto">
				<button
					type="button"
					onclick={() => (showHistory = !showHistory)}
					class="p-2 text-surface-500 hover:text-surface-300 hover:bg-white/5 rounded-lg transition-all duration-200"
					aria-label={showHistory ? 'Hide history' : 'Show history'}
				>
					<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
						<path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16" />
					</svg>
				</button>
				<div class="flex items-center gap-3 min-w-0">
					<span class="text-lg font-semibold text-surface-100 tracking-tight">kGPT</span>
					{#if $currentSession}
						<div class="w-1 h-1 rounded-full bg-surface-600"></div>
						<span class="text-sm text-surface-400 truncate max-w-[300px]">{$currentSession.title}</span>
					{/if}
				</div>
				{#if $chatMessages.length > 0}
					<button
						type="button"
						onclick={handleNewChat}
						class="ml-auto px-3 py-1.5 text-xs font-medium text-surface-400 hover:text-emerald-400 hover:bg-emerald-500/10 rounded-lg transition-all duration-200 flex items-center gap-1.5"
					>
						<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
						</svg>
						New
					</button>
				{/if}
			</div>
		</header>

		<!-- Messages area -->
		<div bind:this={messagesContainer} class="flex-1 overflow-y-auto">
			<div class="max-w-4xl mx-auto px-4 py-8">
				{#if $chatMessages.length === 0}
					<!-- Empty State -->
					<div class="flex flex-col items-center justify-center min-h-[60vh] text-center">
						<!-- Animated icon -->
						<div class="relative mb-10">
							<div class="absolute inset-0 rounded-3xl bg-gradient-to-br from-emerald-500/20 via-cyan-500/10 to-blue-500/20 blur-2xl scale-150 animate-pulse"></div>
							<div class="relative w-24 h-24 rounded-3xl bg-gradient-to-br from-surface-800 to-surface-900 border border-white/10 flex items-center justify-center shadow-2xl shadow-emerald-500/10">
								<svg class="w-12 h-12 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.25">
									<path stroke-linecap="round" stroke-linejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
								</svg>
							</div>
						</div>

						<h2 class="text-3xl font-bold text-surface-100 mb-3 tracking-tight">Ask me anything</h2>
						<p class="text-surface-400 mb-12 max-w-lg leading-relaxed">
							Query your Kafka cluster, search documentation, or perform admin operations.
						</p>

						<!-- Quick Actions -->
						<div class="w-full max-w-2xl space-y-8">
							<!-- Query Section -->
							<div>
								<div class="flex items-center gap-2 mb-4">
									<svg class="w-4 h-4 text-surface-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
										<path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
									</svg>
									<span class="text-xs font-semibold text-surface-500 uppercase tracking-widest">Query & Explore</span>
								</div>
								<div class="grid grid-cols-2 gap-3">
									{#each queryActions as action}
										<button
											type="button"
											onclick={() => handleAction(action)}
											class="action-card group flex items-center gap-4 p-4 text-left rounded-xl bg-surface-900/50 border border-white/5 hover:border-{action.color}-500/30 hover:bg-surface-800/50 transition-all duration-300"
										>
											<div class="flex-shrink-0 w-11 h-11 rounded-xl bg-surface-800/80 border border-white/5 flex items-center justify-center group-hover:border-{action.color}-500/30 group-hover:bg-{action.color}-500/10 transition-all duration-300">
												{#if action.iconType === 'cluster'}
													<svg class="w-5 h-5 text-surface-400 group-hover:text-emerald-400 transition-colors duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
														<path stroke-linecap="round" stroke-linejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
													</svg>
												{:else if action.iconType === 'topics'}
													<svg class="w-5 h-5 text-surface-400 group-hover:text-blue-400 transition-colors duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
														<path stroke-linecap="round" stroke-linejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
													</svg>
												{:else if action.iconType === 'lag'}
													<svg class="w-5 h-5 text-surface-400 group-hover:text-amber-400 transition-colors duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
														<path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
													</svg>
												{:else if action.iconType === 'help'}
													<svg class="w-5 h-5 text-surface-400 group-hover:text-violet-400 transition-colors duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
														<path stroke-linecap="round" stroke-linejoin="round" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
													</svg>
												{/if}
											</div>
											<span class="text-sm font-medium text-surface-300 group-hover:text-surface-100 transition-colors duration-300">{action.label}</span>
										</button>
									{/each}
								</div>
							</div>

							<!-- Admin Section -->
							<div>
								<div class="flex items-center gap-2 mb-4">
									<svg class="w-4 h-4 text-surface-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
										<path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
									</svg>
									<span class="text-xs font-semibold text-surface-500 uppercase tracking-widest">Admin Operations</span>
								</div>
								<div class="grid grid-cols-2 gap-3">
									{#each adminActions as action}
										<button
											type="button"
											onclick={() => handleAction(action)}
											class="action-card group flex items-center gap-4 p-4 text-left rounded-xl bg-surface-900/50 border border-white/5 hover:border-orange-500/20 hover:bg-surface-800/50 transition-all duration-300"
										>
											<div class="flex-shrink-0 w-11 h-11 rounded-xl bg-surface-800/80 border border-white/5 flex items-center justify-center transition-all duration-300">
												{#if action.iconType === 'add'}
													<svg class="w-5 h-5 text-surface-400 group-hover:text-emerald-400 transition-colors duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
														<path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
													</svg>
												{:else if action.iconType === 'delete'}
													<svg class="w-5 h-5 text-surface-400 group-hover:text-red-400 transition-colors duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
														<path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
													</svg>
												{:else if action.iconType === 'settings'}
													<svg class="w-5 h-5 text-surface-400 group-hover:text-blue-400 transition-colors duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
														<path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
														<path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
													</svg>
												{:else if action.iconType === 'partition'}
													<svg class="w-5 h-5 text-surface-400 group-hover:text-violet-400 transition-colors duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
														<path stroke-linecap="round" stroke-linejoin="round" d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
													</svg>
												{/if}
											</div>
											<span class="text-sm font-medium text-surface-300 group-hover:text-surface-100 transition-colors duration-300">{action.label}</span>
										</button>
									{/each}
								</div>
							<p class="flex items-center gap-2 text-xs text-surface-600 mt-4 justify-center">
								<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
									<path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
								</svg>
								<span>Click an action or type naturally — I'll guide you through the details</span>
							</p>
							</div>
						</div>
					</div>
				{:else}
					<!-- Messages -->
					<div class="space-y-10">
						{#each $chatMessages as message (message.id)}
							{#if message.role === 'user'}
								<!-- User Message -->
								<div class="flex justify-end">
									<div class="max-w-[80%] bg-gradient-to-br from-emerald-600/20 to-emerald-600/10 border border-emerald-500/20 rounded-2xl rounded-br-lg px-5 py-3.5 shadow-lg shadow-emerald-500/5">
										<p class="text-surface-100 leading-relaxed text-[15px]">{message.content}</p>
									</div>
								</div>
							{:else}
								<!-- Assistant Message -->
								<div class="space-y-5">
								<!-- Thinking State -->
								{#if message.isThinking && !message.content}
									<div class="flex items-center gap-3 text-surface-400">
										<div class="flex gap-1.5">
											<span class="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style="animation-delay: 0ms"></span>
											<span class="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style="animation-delay: 150ms"></span>
											<span class="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style="animation-delay: 300ms"></span>
										</div>
										<span class="text-sm font-medium">{message.thinkingStage || 'Thinking...'}</span>
									</div>
								{/if}

								<!-- Response Content -->
								{#if message.content}
									<div class="assistant-message-wrapper">
										<FormattedMessage content={message.content} />
									</div>
								{/if}

								<!-- Admin Operation Cards -->
								{#if message.adminResult}
									{@const isExecuting = executingOperationId === message.id}
									{@const warningLevel = message.adminResult.warning_level || 'medium'}

									<!-- NEEDS INFO: Show Input Form Card -->
									{#if message.adminResult.needs_info && message.adminResult.input_fields?.length}
										{@const inputFields = message.adminResult.input_fields}
										{@const _initDefaults = (() => {
											for (const field of inputFields) {
												if (field.default !== null && field.default !== undefined && adminFormValues[field.name] === undefined) {
													adminFormValues[field.name] = field.default;
												}
											}
										})()}
										<div class="mt-4 p-5 bg-surface-900/80 border border-blue-500/30 rounded-xl backdrop-blur-sm shadow-lg shadow-blue-500/5">
											<div class="flex items-center gap-2.5 mb-4">
												<div class="w-9 h-9 rounded-lg bg-blue-500/20 flex items-center justify-center">
													<svg class="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
														<path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
													</svg>
												</div>
												<div>
													<span class="text-sm font-semibold text-blue-400">{message.adminResult.operation_title || 'Configure Operation'}</span>
													<p class="text-xs text-surface-500">Fill in the details below</p>
												</div>
											</div>

											{#if message.adminResult.guidance_message}
												<p class="text-sm text-surface-400 mb-4">{message.adminResult.guidance_message}</p>
											{/if}

											<!-- Input Fields -->
											<div class="space-y-4 mb-4">
												{#each message.adminResult.input_fields as field}
													<div class="group">
														<label class="block text-xs font-medium text-surface-300 mb-2 flex items-center gap-1.5">
															{field.label}
															{#if field.required}
																<span class="text-red-400 text-[10px]">*</span>
															{/if}
														</label>
														{#if field.field_type === 'select' && field.options?.length}
															<div class="relative">
																<select
																	bind:value={adminFormValues[field.name]}
																	class="w-full bg-surface-800/80 border border-white/10 rounded-lg px-3 py-2.5 text-sm text-surface-100 placeholder-surface-500 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all duration-200 appearance-none cursor-pointer hover:border-white/20"
																>
																	<option value="" disabled>{field.placeholder || 'Select an option...'}</option>
																	{#each field.options as option}
																		{@const optionValue = typeof option === 'string' ? option : (option.value || option.label || option)}
																		{@const optionLabel = typeof option === 'string' ? option : (option.label || option.value || option)}
																		<option value={optionValue}>{optionLabel}</option>
																	{/each}
																</select>
																<div class="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
																	<svg class="w-4 h-4 text-surface-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
																		<path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
																	</svg>
																</div>
															</div>
														{:else if field.field_type === 'number'}
															<input
																type="number"
																bind:value={adminFormValues[field.name]}
																placeholder={field.placeholder || String(field.default || '')}
																min="1"
																class="w-full bg-surface-800/80 border border-white/10 rounded-lg px-3 py-2.5 text-sm text-surface-100 placeholder-surface-500 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all duration-200 font-mono hover:border-white/20"
															/>
														{:else}
															<input
																type="text"
																bind:value={adminFormValues[field.name]}
																placeholder={field.placeholder || ''}
																class="w-full bg-surface-800/80 border border-white/10 rounded-lg px-3 py-2.5 text-sm text-surface-100 placeholder-surface-500 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all duration-200 hover:border-white/20"
															/>
														{/if}
														{#if field.hint}
															<p class="text-xs text-surface-500 mt-1.5 ml-0.5 leading-relaxed">{field.hint}</p>
														{/if}
													</div>
												{/each}
											</div>

											<!-- Submit Button -->
											<button
												type="button"
												onclick={() => handleAdminFormSubmit(message.id, message.adminResult?.operation || '', message.adminResult?.params || {})}
												class="w-full px-4 py-2.5 rounded-lg font-medium text-sm bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 border border-blue-500/30 hover:border-blue-500/50 transition-all duration-200 flex items-center justify-center gap-2 shadow-lg shadow-blue-500/10 hover:shadow-blue-500/20"
											>
												<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
													<path stroke-linecap="round" stroke-linejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
												</svg>
												Continue
											</button>
										</div>

									<!-- UNCLEAR: Show Operation Picker Card -->
									{:else if message.adminResult.unclear && message.adminResult.available_operations?.length}
										<div class="mt-4 p-5 bg-surface-900/80 border border-violet-500/30 rounded-xl backdrop-blur-sm shadow-lg shadow-violet-500/5">
											<div class="flex items-center gap-2.5 mb-4">
												<div class="w-9 h-9 rounded-lg bg-violet-500/20 flex items-center justify-center">
													<svg class="w-5 h-5 text-violet-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
														<path stroke-linecap="round" stroke-linejoin="round" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
													</svg>
												</div>
												<div>
													<span class="text-sm font-semibold text-violet-400">Choose an Operation</span>
													<p class="text-xs text-surface-500">{message.adminResult.guidance_message || 'What would you like to do?'}</p>
												</div>
											</div>

											<!-- Operation Buttons -->
											<div class="grid grid-cols-1 gap-2">
												{#each message.adminResult.available_operations as op}
													<button
														type="button"
														onclick={() => handleSelectOperation(op.id)}
														class="flex items-center gap-3 p-3 rounded-lg bg-surface-800/60 border border-white/5 hover:border-violet-500/30 hover:bg-surface-800 transition-all duration-200 text-left group"
													>
														<div class="w-8 h-8 rounded-lg bg-surface-700 flex items-center justify-center group-hover:bg-violet-500/20 transition-colors">
															{#if op.icon === 'add'}
																<svg class="w-4 h-4 text-surface-400 group-hover:text-violet-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
																	<path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
																</svg>
															{:else if op.icon === 'delete'}
																<svg class="w-4 h-4 text-surface-400 group-hover:text-violet-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
																	<path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
																</svg>
															{:else if op.icon === 'settings'}
																<svg class="w-4 h-4 text-surface-400 group-hover:text-violet-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
																	<path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
																	<path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
																</svg>
															{:else if op.icon === 'partition'}
																<svg class="w-4 h-4 text-surface-400 group-hover:text-violet-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
																	<path stroke-linecap="round" stroke-linejoin="round" d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
																</svg>
															{:else}
																<svg class="w-4 h-4 text-surface-400 group-hover:text-violet-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
																	<path stroke-linecap="round" stroke-linejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
																</svg>
															{/if}
														</div>
														<span class="text-sm text-surface-300 group-hover:text-surface-100 transition-colors">{op.label}</span>
														<svg class="w-4 h-4 text-surface-600 group-hover:text-violet-400 ml-auto transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
															<path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
														</svg>
													</button>
												{/each}
											</div>
										</div>

									<!-- PENDING: Show Confirmation Card -->
									{:else if message.adminResult.pending}
										<div class="mt-4 p-5 bg-surface-900/80 border rounded-xl backdrop-blur-sm
											{warningLevel === 'high' ? 'border-amber-500/40 shadow-lg shadow-amber-500/10' :
											 warningLevel === 'medium' ? 'border-blue-500/30 shadow-lg shadow-blue-500/5' :
											 'border-emerald-500/30 shadow-lg shadow-emerald-500/5'}">
											<div class="flex items-center gap-2.5 mb-4">
												<div class="w-9 h-9 rounded-lg flex items-center justify-center
													{warningLevel === 'high' ? 'bg-amber-500/20' :
													 warningLevel === 'medium' ? 'bg-blue-500/20' :
													 'bg-emerald-500/20'}">
													{#if warningLevel === 'high'}
														<svg class="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
															<path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
														</svg>
													{:else}
														<svg class="w-5 h-5 {warningLevel === 'medium' ? 'text-blue-400' : 'text-emerald-400'}" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
															<path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
														</svg>
													{/if}
												</div>
												<div>
													<span class="text-sm font-semibold
														{warningLevel === 'high' ? 'text-amber-400' :
														 warningLevel === 'medium' ? 'text-blue-400' :
														 'text-emerald-400'}">
														{message.adminResult.operation_title || 'Confirm Operation'}
													</span>
													<p class="text-xs text-surface-500">Review and confirm to execute</p>
												</div>
											</div>

											<!-- Operation Summary -->
											<div class="bg-surface-800/60 rounded-lg p-4 mb-4 border border-white/5">
												<div class="text-sm text-surface-300 space-y-2">
													{#each Object.entries(message.adminResult.params || {}) as [key, value]}
														<div class="flex items-center gap-3">
															<span class="text-surface-500 text-xs uppercase tracking-wider min-w-[80px]">{key.replace(/_/g, ' ')}</span>
															<span class="font-mono text-emerald-400">{value}</span>
														</div>
													{/each}
												</div>
											</div>

											{#if message.adminResult.warning_message}
												<div class="flex items-start gap-2 p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg mb-4">
													<svg class="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
														<path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
													</svg>
													<p class="text-sm text-amber-300">{message.adminResult.warning_message}</p>
												</div>
											{/if}

											{#if message.adminResult.confirmation_message}
												<p class="text-sm text-surface-400 mb-4">{message.adminResult.confirmation_message}</p>
											{/if}

											<!-- Buttons -->
											<div class="flex gap-3">
												<button
													type="button"
													disabled={isExecuting}
													onclick={() => handleConfirmOperation(message.id, message.adminResult?.operation || '', message.adminResult?.params || {})}
													class="flex-1 px-4 py-2.5 rounded-lg font-medium text-sm transition-all duration-200 flex items-center justify-center gap-2
														{warningLevel === 'high'
															? 'bg-amber-500/20 hover:bg-amber-500/30 text-amber-400 border border-amber-500/30 hover:border-amber-500/50'
															: 'bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 border border-emerald-500/30 hover:border-emerald-500/50'}
														disabled:opacity-50 disabled:cursor-not-allowed"
												>
													{#if isExecuting}
														<svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
															<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
															<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
														</svg>
														<span>Executing...</span>
													{:else}
														<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
															<path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
														</svg>
														<span>Confirm & Execute</span>
													{/if}
												</button>
												<button
													type="button"
													disabled={isExecuting}
													onclick={() => handleCancelOperation(message.id)}
													class="px-4 py-2.5 rounded-lg font-medium text-sm bg-surface-700/50 hover:bg-surface-600/50 text-surface-300 border border-white/5 hover:border-white/10 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
												>
													Cancel
												</button>
											</div>
										</div>

									<!-- ERROR: Show Error Card -->
									{:else if message.adminResult.error}
										<div class="mt-4 p-5 bg-surface-900/80 border border-red-500/30 rounded-xl backdrop-blur-sm shadow-lg shadow-red-500/5">
											<div class="flex items-center gap-2.5 mb-3">
												<div class="w-8 h-8 rounded-lg bg-red-500/20 flex items-center justify-center">
													<svg class="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
														<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
													</svg>
												</div>
												<span class="text-sm font-semibold text-red-400">Operation Failed</span>
											</div>
											<p class="text-sm text-red-300 font-mono">{message.adminResult.error}</p>
										</div>

									<!-- SUCCESS/CANCELLED: Show Result Card -->
									{:else if message.adminResult.success === true || message.adminResult.operation === 'cancelled'}
										<div class="mt-4 p-5 bg-surface-900/80 border rounded-xl backdrop-blur-sm {message.adminResult.operation === 'cancelled' ? 'border-surface-600' : 'border-emerald-500/30 shadow-lg shadow-emerald-500/5'}">
											<div class="flex items-center gap-2.5 mb-3">
												{#if message.adminResult.operation === 'cancelled'}
													<div class="w-8 h-8 rounded-lg bg-surface-600/50 flex items-center justify-center">
														<svg class="w-5 h-5 text-surface-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
															<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
														</svg>
													</div>
													<span class="text-sm font-semibold text-surface-400">Operation Cancelled</span>
												{:else}
													<div class="w-8 h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center">
														<svg class="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
															<path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
														</svg>
													</div>
													<span class="text-sm font-semibold text-emerald-400">Operation Successful</span>
												{/if}
											</div>
											{#if message.adminResult.message}
												<p class="text-sm text-surface-300">{message.adminResult.message}</p>
											{/if}
											{#if message.adminResult.topic}
												<p class="text-sm text-surface-400 font-mono mt-2">Topic: {message.adminResult.topic}</p>
											{/if}
										</div>
									{/if}
								{/if}

									<!-- Cluster Context Card -->
									{#if message.clusterContext}
										{@const brokerCount = message.clusterContext.broker_count ?? (typeof message.clusterContext.brokers === 'number' ? message.clusterContext.brokers : Object.keys(message.clusterContext.brokers || {}).length)}
										{@const topicCount = message.clusterContext.topic_count ?? message.clusterContext.topics?.length ?? 0}
										{@const groupCount = message.clusterContext.consumer_groups?.length ?? 0}
										<MessageCard
											title="Cluster Overview"
											iconType="cluster"
											iconColor="emerald"
											variant="success"
										>
											{#if message.clusterContext.cluster_id}
												<div class="flex items-center justify-end mb-3">
													<span class="text-xs text-surface-500 font-mono">{message.clusterContext.cluster_id.slice(0, 12)}...</span>
												</div>
											{/if}
											<div class="grid grid-cols-3 gap-6">
												<MetricCard value={brokerCount} label="Brokers" />
												<MetricCard value={topicCount} label="Topics" />
												<MetricCard value={groupCount} label="Groups" />
											</div>
										</MessageCard>
									{/if}

									<!-- Suggested Actions -->
									{#if message.actions && message.actions.length > 0 && !message.isStreaming}
										<div class="flex flex-wrap gap-2 mt-4">
											{#each message.actions as action}
												<button
													type="button"
													onclick={() => handleSuggestedAction(action)}
													class="inline-flex items-center gap-2 px-4 py-2 text-sm bg-surface-800/80 hover:bg-surface-700/80 border border-white/5 hover:border-white/10 rounded-full text-surface-300 hover:text-surface-100 transition-all duration-200"
												>
													{action.label}
													<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
														<path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
													</svg>
												</button>
											{/each}
										</div>
									{/if}

									<!-- Citations -->
									{#if message.citations && message.citations.length > 0 && !message.isStreaming}
										<details class="mt-4 group">
											<summary class="text-xs text-surface-500 cursor-pointer hover:text-surface-400 flex items-center gap-1.5 transition-colors">
												<svg class="w-3.5 h-3.5 transition-transform group-open:rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
													<path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
												</svg>
												{message.citations.length} source{message.citations.length !== 1 ? 's' : ''}
											</summary>
											<div class="mt-3 pl-4 border-l-2 border-surface-700 space-y-1.5">
												{#each message.citations as citation}
													<a
														href={citation}
														target="_blank"
														rel="noopener noreferrer"
														class="block text-xs text-blue-400 hover:text-blue-300 truncate transition-colors"
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

		<!-- Input Area -->
		<div class="border-t border-white/5 bg-surface-900/60 backdrop-blur-xl p-4">
			<div class="max-w-4xl mx-auto">
				<div class="relative flex items-end gap-3 bg-surface-800/80 border border-white/10 rounded-2xl p-3 focus-within:border-emerald-500/40 focus-within:ring-2 focus-within:ring-emerald-500/10 transition-all duration-300">
					<textarea
						bind:this={inputRef}
						bind:value={inputValue}
						onkeydown={handleKeydown}
						placeholder="Ask about your cluster or documentation..."
						disabled={$isProcessing}
						rows="1"
						class="flex-1 bg-transparent text-surface-100 placeholder-surface-500 resize-none focus:outline-none disabled:opacity-50 px-2 py-1.5 max-h-36 text-[15px]"
						style="field-sizing: content;"
					></textarea>
					<button
						type="button"
						onclick={() => sendMessage(inputValue)}
						disabled={$isProcessing || !inputValue.trim()}
						class="flex-shrink-0 w-10 h-10 flex items-center justify-center bg-emerald-600 hover:bg-emerald-500 disabled:bg-surface-700 disabled:text-surface-500 text-white rounded-xl transition-all duration-200 hover:scale-105 active:scale-95 disabled:hover:scale-100"
					>
						{#if $isProcessing}
							<svg class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
								<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
								<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
							</svg>
						{:else}
							<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
								<path stroke-linecap="round" stroke-linejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
							</svg>
						{/if}
					</button>
				</div>
				<p class="text-center text-xs text-surface-600 mt-3">
					Press Enter to send <span class="text-surface-700 mx-1">|</span> Shift+Enter for new line
				</p>
			</div>
		</div>
	</div>
</div>

<style>
	@reference "../app.css";

	.chat-page {
		--action-glow: 0 4px 24px rgba(16, 185, 129, 0.15);
	}

	.action-card {
		position: relative;
		overflow: hidden;
	}

	.action-card::before {
		content: '';
		position: absolute;
		inset: 0;
		background: linear-gradient(135deg, rgba(52, 211, 153, 0.1) 0%, transparent 50%);
		opacity: 0;
		transition: opacity 300ms ease;
	}

	.action-card:hover::before {
		opacity: 1;
	}

	.action-card:hover {
		box-shadow: var(--action-glow);
		transform: translateY(-2px);
		border-color: rgba(52, 211, 153, 0.3) !important;
	}

	.action-card:active {
		transform: translateY(0);
	}

	/* Smooth scrollbar */
	.chat-page ::-webkit-scrollbar {
		width: 6px;
	}

	.chat-page ::-webkit-scrollbar-track {
		background: transparent;
	}

	.chat-page ::-webkit-scrollbar-thumb {
		background: rgb(71 85 105 / 0.5);
		border-radius: 3px;
	}

	.chat-page ::-webkit-scrollbar-thumb:hover {
		background: rgb(100 116 139 / 0.6);
	}

	/* Enhanced assistant message styling */
	.assistant-message-wrapper {
		@apply max-w-full;
		line-height: 1.7;
	}

	.assistant-message-wrapper :global(.formatted-message) {
		color: rgb(var(--color-surface-200));
		font-size: 15px;
	}

	.assistant-message-wrapper :global(.formatted-message > *:first-child) {
		@apply mt-0;
	}

	.assistant-message-wrapper :global(.formatted-message > *:last-child) {
		@apply mb-0;
	}

	/* Better visual separation for structured content */
	.assistant-message-wrapper :global(.formatted-message h1),
	.assistant-message-wrapper :global(.formatted-message h2),
	.assistant-message-wrapper :global(.formatted-message h3) {
		@apply border-b border-white/5 pb-2 mb-4;
	}
</style>
