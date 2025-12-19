<script lang="ts">
	import { Button } from '$lib/components/ui';
	import {
		AgentTimelineItem,
		RoutingDecisionCard,
		RetrievalResultsList,
		WebResultsList
	} from '$lib/components/agent-trace';
	import {
		displayedAgentTrace,
		selectedMessageId,
		selectMessageForTrace,
		isProcessing
	} from '$lib/stores/chat';

	interface Props {
		onClose: () => void;
	}

	let { onClose }: Props = $props();

	let expandedSections = $state<Record<string, boolean>>({});

	function toggleSection(section: string) {
		expandedSections = { ...expandedSections, [section]: !expandedSections[section] };
	}

	let trace = $derived($displayedAgentTrace);
	let isViewingHistory = $derived($selectedMessageId !== null);
	let isStreaming = $derived($isProcessing);
	let hasContent = $derived(trace.agentTimeline.length > 0 || trace.routingDecision !== null);

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') onClose();
	}
</script>

<svelte:window onkeydown={handleKeydown} />

<!-- Backdrop -->
<div
	class="fixed inset-0 bg-black/40 backdrop-blur-sm z-50"
	onclick={onClose}
	onkeydown={(e) => e.key === 'Escape' && onClose()}
	role="button"
	tabindex="-1"
></div>

<!-- Drawer -->
<aside class="fixed top-0 right-0 bottom-0 w-full max-w-md bg-surface-900 border-l border-surface-700/50 z-50 flex flex-col shadow-2xl animate-slide-in-right">
	<!-- Header -->
	<header class="flex items-center justify-between px-4 py-3 border-b border-surface-700/50 bg-surface-800/50">
		<div class="flex items-center gap-3">
			<div class="w-8 h-8 rounded-lg bg-violet-500/10 flex items-center justify-center">
				<svg class="w-4 h-4 text-violet-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
					<path stroke-linecap="round" stroke-linejoin="round" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
				</svg>
			</div>
			<div>
				<h2 class="font-semibold text-surface-100">Agent Pipeline</h2>
				<p class="text-xs text-surface-500">
					{#if isViewingHistory}
						Viewing saved trace
					{:else if isStreaming}
						<span class="text-violet-400">Live</span>
					{:else}
						AI reasoning process
					{/if}
				</p>
			</div>
		</div>
		<div class="flex items-center gap-2">
			{#if isViewingHistory}
				<Button variant="ghost" size="sm" onclick={() => selectMessageForTrace(null)}>
					Show Live
				</Button>
			{/if}
			<Button variant="ghost" size="icon" onclick={onClose}>
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
					<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</Button>
		</div>
	</header>

	<!-- Content -->
	<div class="flex-1 overflow-y-auto p-4">
		{#if !hasContent}
			<div class="flex flex-col items-center justify-center h-full text-center py-8">
				<div class="w-16 h-16 rounded-2xl bg-surface-800 flex items-center justify-center mb-4">
					<svg class="w-8 h-8 text-surface-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1">
						<path stroke-linecap="round" stroke-linejoin="round" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
					</svg>
				</div>
				<h3 class="text-lg font-semibold text-surface-300 mb-2">No Activity Yet</h3>
				<p class="text-sm text-surface-500 max-w-xs">
					{#if isViewingHistory}
						This message doesn't have trace data
					{:else}
						Send a message to see the AI pipeline in action
					{/if}
				</p>
			</div>
		{:else}
			<div class="space-y-4">
				<!-- Agent Timeline -->
				{#each trace.agentTimeline as activity}
					<AgentTimelineItem
						{activity}
						expanded={expandedSections[activity.agent] ?? false}
						onToggle={() => toggleSection(activity.agent)}
					/>
				{/each}

				<!-- Routing Decision -->
				{#if trace.routingDecision}
					<RoutingDecisionCard
						decision={trace.routingDecision}
						expanded={expandedSections['routing'] ?? false}
						onToggle={() => toggleSection('routing')}
					/>
				{/if}

				<!-- Retrieval Results -->
				{#if trace.retrievalResults}
					<RetrievalResultsList
						results={trace.retrievalResults}
						expanded={expandedSections['retrieval_results'] ?? false}
						onToggle={() => toggleSection('retrieval_results')}
					/>
				{/if}

				<!-- Web Search Results -->
				{#if trace.webSearchResults}
					<WebResultsList
						results={trace.webSearchResults}
						expanded={expandedSections['web_results'] ?? false}
						onToggle={() => toggleSection('web_results')}
					/>
				{/if}
			</div>
		{/if}
	</div>

	<!-- Footer -->
	<footer class="px-4 py-3 border-t border-surface-700/50 bg-surface-800/30">
		<p class="text-xs text-surface-500 text-center">
			View the AI's decision-making process
		</p>
	</footer>
</aside>
