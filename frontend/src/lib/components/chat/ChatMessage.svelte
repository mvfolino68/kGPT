<script lang="ts">
	import { RetroButton, RetroCard, StatusIndicator } from '$lib/components';
	import { SourceDrawer } from '$lib/components/sources';
	import { normalizeCitation, type Source } from '$lib/components/sources/types';
	import { renderMarkdown } from '$lib/utils/markdown';
	import { selectedMessageId, selectMessageForTrace, type MessageAgentTrace } from '$lib/stores/chat';

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
		};
		onActionClick: (value: string) => void;
	}

	let { message, onActionClick }: Props = $props();

	// State for source drawer
	let selectedSource = $state<Source | null>(null);

	// State for expanding sources list
	let sourcesExpanded = $state(false);

	// Check if this message is selected for trace viewing
	let isSelected = $derived($selectedMessageId === message.id);

	// Check if this message has trace data
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

	/**
	 * Convert legacy citations to unified Source format.
	 * This handles both old URL strings and new structured citations.
	 */
	function normalizeSources(citations: unknown[] | undefined): Source[] {
		if (!citations || citations.length === 0) return [];

		return citations.map((c, index) => {
			const source = normalizeCitation(c);
			// Add an ID if not present
			if (!source.id) {
				source.id = `source-${index + 1}`;
			}
			return source;
		});
	}

	const sources = $derived(normalizeSources(message.citations));

	/**
	 * Handle clicks on citation buttons in the rendered markdown.
	 */
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
	<!-- Assistant Message -->
	<div class="flex justify-start animate-slide-in-left">
		<div class="max-w-[85%] space-y-3">
			<!-- Thinking indicator -->
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

			<!-- Message content -->
			{#if message.content}
				<RetroCard variant="glow-blue" class="!p-0 {isSelected ? 'ring-1 ring-violet-500/50' : ''}">
					<div class="px-4 py-3">
						<!-- Header -->
						<div class="flex items-center gap-2 mb-3">
							<span class="text-[10px] font-mono text-confluent-primary uppercase tracking-wider">kGPT</span>
							<StatusIndicator status="active" size="sm" />
							{#if message.isStreaming}
								<span class="text-[9px] font-mono text-surface-500 animate-pulse">streaming...</span>
							{/if}
							<!-- Trace indicator button -->
							{#if hasTrace && !message.isStreaming}
								<button
									type="button"
									onclick={handleTraceClick}
									class="ml-auto flex items-center gap-1 px-2 py-0.5 rounded text-[9px] font-mono transition-colors {isSelected ? 'bg-violet-500/20 text-violet-400 border border-violet-500/30' : 'text-surface-500 hover:text-violet-400 hover:bg-violet-500/10'}"
									title="View agent pipeline trace"
								>
									<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
										<path stroke-linecap="round" stroke-linejoin="round" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
									</svg>
									<span>{isSelected ? 'Hide Trace' : 'View Trace'}</span>
								</button>
							{/if}
						</div>

						<!-- Markdown content with inline citations (clickable) -->
						<!-- svelte-ignore a11y_click_events_have_key_events -->
						<!-- svelte-ignore a11y_no_static_element_interactions -->
						<div
							class="prose prose-sm prose-invert max-w-none text-sm leading-relaxed message-content"
							onclick={handleContentClick}
						>
							{@html renderMarkdown(message.content)}
						</div>

						<!-- Sources section -->
						{#if sources.length > 0 && !message.isStreaming}
							<div class="mt-3 pt-3 border-t border-surface-700/50">
								<!-- Toggle button -->
								<button
									type="button"
									class="flex items-center gap-2 text-xs text-surface-400 hover:text-cyan-400 transition-colors"
									onclick={() => sourcesExpanded = !sourcesExpanded}
								>
									<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
										<path stroke-linecap="round" stroke-linejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
									</svg>
									<span>{sources.length} {sources.length === 1 ? 'Source' : 'Sources'}</span>
									<svg
										class="w-3 h-3 transition-transform duration-200 {sourcesExpanded ? 'rotate-180' : ''}"
										fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"
									>
										<path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
									</svg>
								</button>

								<!-- Simple sources list -->
								{#if sourcesExpanded}
									<ul class="mt-2 space-y-1">
										{#each sources as source, i}
											<li>
												<button
													type="button"
													class="w-full text-left px-2 py-1.5 rounded text-xs font-mono
														text-surface-300 hover:text-cyan-400 hover:bg-surface-800/50
														transition-colors flex items-center gap-2"
													onclick={() => selectedSource = source}
												>
													<span class="text-cyan-500/70">[{i + 1}]</span>
													<span class="truncate">{source.title}</span>
												</button>
											</li>
										{/each}
									</ul>
								{/if}
							</div>
						{/if}
					</div>
				</RetroCard>
			{/if}

			<!-- Suggested Actions -->
			{#if message.actions && message.actions.length > 0 && !message.isStreaming}
				<div class="flex flex-wrap gap-2 pt-1">
					{#each message.actions as action}
						<RetroButton size="sm" onclick={() => onActionClick(action.value)}>
							{action.label}
						</RetroButton>
					{/each}
				</div>
			{/if}
		</div>
	</div>
{/if}

<!-- Source drawer for viewing citation details -->
<SourceDrawer source={selectedSource} onClose={closeDrawer} />

<style>
	/* Prose styling for markdown content */
	:global(.message-content p) {
		margin: 0.5rem 0;
		color: rgb(var(--color-surface-200));
	}
	:global(.message-content p:first-child) {
		margin-top: 0;
	}
	:global(.message-content p:last-child) {
		margin-bottom: 0;
	}
	:global(.message-content ul), :global(.message-content ol) {
		margin: 0.5rem 0;
		padding-left: 1.5rem;
	}
	:global(.message-content li) {
		margin: 0.25rem 0;
	}
	:global(.message-content code) {
		background: rgba(var(--color-surface-800), 0.8);
		padding: 0.125rem 0.375rem;
		border-radius: 0.25rem;
		font-size: 0.875em;
		color: rgb(var(--confluent-accent));
		border: 1px solid rgba(var(--confluent-accent), 0.2);
	}
	:global(.message-content pre) {
		background: rgb(var(--color-surface-900));
		border: 1px solid rgba(255, 255, 255, 0.1);
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
		color: rgb(var(--confluent-primary));
	}
	:global(.message-content a) {
		color: rgb(var(--retro-cyan));
		text-decoration: underline;
	}
	:global(.message-content blockquote) {
		border-left: 3px solid rgba(var(--confluent-primary), 0.3);
		padding-left: 1rem;
		margin: 0.75rem 0;
		color: rgb(var(--color-surface-400));
	}

	/* Citation references - clickable inline superscript buttons */
	:global(.citation-ref) {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		min-width: 1.25rem;
		height: 1.25rem;
		padding: 0 0.25rem;
		margin: 0 0.125rem;
		font-family: var(--font-mono);
		font-size: 0.65em;
		font-weight: 700;
		color: rgb(var(--retro-cyan));
		background: rgba(var(--retro-cyan), 0.1);
		border: 1px solid rgba(var(--retro-cyan), 0.3);
		border-radius: 0.25rem;
		cursor: pointer;
		vertical-align: super;
		line-height: 1;
		transition: all 0.15s ease;
	}
	:global(.citation-ref:hover) {
		background: rgba(var(--retro-cyan), 0.25);
		border-color: rgba(var(--retro-cyan), 0.6);
		transform: scale(1.1);
		box-shadow: 0 0 8px rgba(var(--retro-cyan), 0.3);
	}
	:global(.citation-ref:active) {
		transform: scale(0.95);
	}
</style>
