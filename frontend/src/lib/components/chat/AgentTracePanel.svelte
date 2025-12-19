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
</script>

<aside class="w-80 bg-surface-900 border-l border-surface-700/50 flex flex-col">
	<!-- Header -->
	<header class="flex items-center justify-between px-3 py-3 border-b border-surface-700/50 bg-surface-800/50">
		<div class="flex items-center gap-2">
			<div class="w-6 h-6 rounded bg-violet-500/10 flex items-center justify-center">
				<svg class="w-3.5 h-3.5 text-violet-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
					<path stroke-linecap="round" stroke-linejoin="round" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
				</svg>
			</div>
			<div>
				<h2 class="text-sm font-medium text-surface-200">Pipeline</h2>
				<p class="text-[10px] text-surface-500">
					{#if isViewingHistory}
						Saved trace
					{:else if isStreaming}
						<span class="text-violet-400 flex items-center gap-1">
							<span class="w-1 h-1 rounded-full bg-violet-400 animate-pulse"></span>
							Live
						</span>
					{:else}
						AI reasoning
					{/if}
				</p>
			</div>
		</div>
		<div class="flex items-center gap-1">
			{#if isViewingHistory}
				<button
					type="button"
					class="px-2 py-1 text-[10px] font-medium text-violet-400 hover:text-violet-300 hover:bg-violet-500/10 rounded transition-colors"
					onclick={() => selectMessageForTrace(null)}
				>
					Live
				</button>
			{/if}
			<button
				type="button"
				class="p-1.5 text-surface-500 hover:text-surface-300 hover:bg-surface-700/50 rounded transition-colors"
				onclick={onClose}
				title="Hide panel"
			>
				<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
					<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</button>
		</div>
	</header>

	<!-- Content -->
	<div class="flex-1 overflow-y-auto p-3">
		{#if !hasContent}
			<div class="flex flex-col items-center justify-center h-full text-center py-8">
				<div class="w-12 h-12 rounded-xl bg-surface-800 flex items-center justify-center mb-3">
					<svg class="w-6 h-6 text-surface-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1">
						<path stroke-linecap="round" stroke-linejoin="round" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
					</svg>
				</div>
				<p class="text-xs text-surface-400 mb-1">No activity yet</p>
				<p class="text-[10px] text-surface-600 max-w-[180px]">
					{#if isViewingHistory}
						This message has no trace data
					{:else}
						Send a message to see the pipeline
					{/if}
				</p>
			</div>
		{:else}
			<div class="space-y-2">
				<!-- Agent Timeline -->
				{#each trace.agentTimeline as activity}
					<AgentTimelineItem
						{activity}
						expanded={expandedSections[activity.agent] ?? false}
						onToggle={() => toggleSection(activity.agent)}
						compact
					/>
				{/each}

				<!-- Routing Decision -->
				{#if trace.routingDecision}
					<RoutingDecisionCard
						decision={trace.routingDecision}
						expanded={expandedSections['routing'] ?? false}
						onToggle={() => toggleSection('routing')}
						compact
					/>
				{/if}

				<!-- Retrieval Results -->
				{#if trace.retrievalResults}
					<RetrievalResultsList
						results={trace.retrievalResults}
						expanded={expandedSections['retrieval_results'] ?? false}
						onToggle={() => toggleSection('retrieval_results')}
						maxItems={4}
						compact
					/>
				{/if}

				<!-- Web Search Results -->
				{#if trace.webSearchResults}
					<WebResultsList
						results={trace.webSearchResults}
						expanded={expandedSections['web_results'] ?? false}
						onToggle={() => toggleSection('web_results')}
						maxItems={4}
						compact
					/>
				{/if}
			</div>
		{/if}
	</div>

	<!-- Footer -->
	<footer class="px-3 py-2 border-t border-surface-700/50 bg-surface-800/30">
		<p class="text-[10px] text-surface-600 text-center">
			AI decision process
		</p>
	</footer>
</aside>
