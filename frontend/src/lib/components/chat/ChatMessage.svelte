<script lang="ts">
	import { StatusIndicator } from '$lib/components';
	import { AdminResultCard } from '$lib/components/admin';
	import { SourceDrawer } from '$lib/components/sources';
	import { normalizeCitation, type Source } from '$lib/components/sources/types';
	import { renderMarkdown } from '$lib/utils/markdown';
	import { selectedMessageId, selectMessageForTrace, updateMessage, type MessageAgentTrace, type AdminOperationResult } from '$lib/stores/chat';
	import { ThinkingIndicator, MessageActions, SourcesList } from './message';

	interface Props {
		message: {
			id: string;
			role: 'user' | 'assistant';
			content: string;
			isStreaming?: boolean;
			isThinking?: boolean;
			thinkingStage?: string;
			citations?: unknown[];
			actions?: Array<{ label: string; value: string }>;
			agentTrace?: MessageAgentTrace;
			adminResult?: AdminOperationResult;
		};
		onActionClick: (value: string) => void;
	}

	let { message, onActionClick }: Props = $props();

	let selectedSource = $state<Source | null>(null);

	let isSelected = $derived($selectedMessageId === message.id);
	let hasTrace = $derived(
		message.agentTrace &&
		(message.agentTrace.agentTimeline.length > 0 || message.agentTrace.routingDecision)
	);

	function handleTraceClick(event: MouseEvent) {
		event.stopPropagation();
		if (hasTrace) {
			selectMessageForTrace(isSelected ? null : message.id);
		}
	}

	function handleAdminOperationComplete(result: AdminOperationResult) {
		updateMessage(message.id, { adminResult: result });
	}

	function normalizeSources(citations: unknown[] | undefined): Source[] {
		if (!citations || citations.length === 0) return [];
		return citations.map((c, index) => {
			const source = normalizeCitation(c);
			if (!source.id) source.id = `source-${index + 1}`;
			return source;
		});
	}

	const sources = $derived(normalizeSources(message.citations));

	function handleContentClick(event: MouseEvent) {
		const target = event.target as HTMLElement;
		if (target.classList.contains('citation-ref')) {
			const index = parseInt(target.dataset.citationIndex || '0', 10);
			if (index > 0 && index <= sources.length) {
				selectedSource = sources[index - 1];
			}
		}
	}

	function closeDrawer() {
		selectedSource = null;
	}
</script>

{#if message.role === 'user'}
	<!-- User Message -->
	<div class="flex justify-end animate-fade-in">
		<div class="max-w-[75%] bg-surface-800 rounded-lg px-4 py-3">
			<div class="flex items-center gap-2 mb-2">
				<span class="text-[10px] font-bold uppercase tracking-wider text-surface-400">USER</span>
			</div>
			<p class="text-surface-100 text-sm leading-relaxed">{message.content}</p>
		</div>
	</div>
{:else}
	<!-- Assistant Message -->
	<div class="flex justify-start animate-fade-in">
		<div class="max-w-[85%] space-y-3">
			<!-- Thinking indicator -->
			{#if message.isThinking && !message.content}
				<ThinkingIndicator stage={message.thinkingStage} />
			{/if}

			<!-- Message content -->
			{#if message.content}
				<div class="bg-surface-800 rounded-lg {isSelected ? 'ring-1 ring-violet-500/50' : ''}">
					<div class="px-4 py-3">
						<!-- Header -->
						<div class="flex items-center gap-2 mb-3">
							<span class="text-[10px] font-bold uppercase tracking-wider text-primary-light">kGPT</span>
							<StatusIndicator status="active" size="sm" />
							{#if message.isStreaming}
								<span class="text-[9px] text-surface-500 animate-pulse">streaming...</span>
							{/if}
							{#if hasTrace && !message.isStreaming}
								<button
									type="button"
									onclick={handleTraceClick}
									class="ml-auto flex items-center gap-1 px-2 py-0.5 rounded text-[9px] transition-colors
										{isSelected
											? 'bg-surface-700/60 text-surface-200'
											: 'text-surface-500 hover:text-surface-300 hover:bg-surface-700/40'}"
									title="View agent pipeline trace"
								>
									<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
										<path stroke-linecap="round" stroke-linejoin="round" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
									</svg>
									<span>{isSelected ? 'Hide Trace' : 'View Trace'}</span>
								</button>
							{/if}
						</div>

						<!-- Markdown content -->
						<!-- svelte-ignore a11y_click_events_have_key_events -->
						<!-- svelte-ignore a11y_no_static_element_interactions -->
						<div
							class="prose prose-sm prose-invert max-w-none text-sm leading-relaxed message-content"
							onclick={handleContentClick}
						>
							{@html renderMarkdown(message.content)}
						</div>

						<!-- Sources section -->
						{#if !message.isStreaming}
							<SourcesList {sources} onSourceClick={(s) => selectedSource = s} />
						{/if}
					</div>
				</div>
			{/if}

			<!-- Admin Operation Result -->
			{#if message.adminResult && (!message.isStreaming || message.adminResult.pending || message.adminResult.needs_info || message.adminResult.unclear)}
				<AdminResultCard result={message.adminResult} onOperationComplete={handleAdminOperationComplete} />
			{/if}

			<!-- Suggested Actions -->
			{#if message.actions && !message.isStreaming}
				<MessageActions actions={message.actions} {onActionClick} />
			{/if}
		</div>
	</div>
{/if}

<SourceDrawer source={selectedSource} onClose={closeDrawer} />

<style>
	/* Prose styling for markdown content */
	:global(.message-content p) {
		margin: 0.5rem 0;
		color: rgb(var(--color-surface-200));
	}
	:global(.message-content p:first-child) { margin-top: 0; }
	:global(.message-content p:last-child) { margin-bottom: 0; }

	:global(.message-content ul), :global(.message-content ol) {
		margin: 0.5rem 0;
		padding-left: 1.5rem;
	}
	:global(.message-content li) { margin: 0.25rem 0; }

	:global(.message-content code) {
		background: rgba(var(--color-surface-700), 0.5);
		padding: 0.125rem 0.375rem;
		border-radius: 0.25rem;
		font-size: 0.875em;
		color: rgb(var(--color-surface-200));
	}

	:global(.message-content pre) {
		background: rgb(var(--color-surface-900));
		border-radius: 0.5rem;
		padding: 1rem;
		overflow-x: auto;
		margin: 0.75rem 0;
	}
	:global(.message-content pre code) {
		background: transparent;
		padding: 0;
		border: none;
	}

	:global(.message-content h1),
	:global(.message-content h2),
	:global(.message-content h3) {
		margin-top: 1rem;
		margin-bottom: 0.5rem;
		font-weight: 600;
		color: rgb(var(--color-primary-light));
	}

	:global(.message-content a) {
		color: rgb(var(--color-accent));
		text-decoration: underline;
	}

	:global(.message-content blockquote) {
		border-left: 3px solid rgba(var(--color-surface-600), 0.5);
		padding-left: 1rem;
		margin: 0.75rem 0;
		color: rgb(var(--color-surface-400));
	}

	/* Citation references */
	:global(.citation-ref) {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		min-width: 1.25rem;
		height: 1.25rem;
		padding: 0 0.25rem;
		margin: 0 0.125rem;
		font-size: 0.65em;
		font-weight: 700;
		color: rgb(var(--color-accent));
		background: rgba(var(--color-accent), 0.15);
		border-radius: 0.25rem;
		cursor: pointer;
		vertical-align: super;
		line-height: 1;
		transition: all 0.15s ease;
	}
	:global(.citation-ref:hover) {
		background: rgba(var(--color-accent), 0.3);
		transform: scale(1.1);
	}

	/* Text selection */
	:global(.message-content) {
		-webkit-user-select: text;
		user-select: text;
	}
	:global(.message-content ::selection) {
		background: rgba(255, 235, 59, 0.65);
		color: inherit;
	}

	/* Image styling */
	:global(.message-content .markdown-image-container) {
		position: relative;
		margin: 1rem 0;
		border-radius: 0.5rem;
		overflow: hidden;
		background: rgb(var(--color-surface-900) / 0.3);
	}
	:global(.message-content .markdown-image) {
		width: 100%;
		height: auto;
		display: block;
	}
	:global(.message-content img) {
		max-width: 100%;
		height: auto;
	}
</style>
