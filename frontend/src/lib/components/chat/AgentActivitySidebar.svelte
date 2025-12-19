<script lang="ts">
	import { Button, Icon, IconButton } from '$lib/components/ui';
	import {
		AgentTimelineItem,
		RoutingDecisionCard,
		RetrievalResultsList,
		WebResultsList
	} from '$lib/components/agent-trace';
	import {
		displayedAgentTrace,
		selectedMessageId,
		showAgentActivity,
		toggleAgentActivity,
		selectMessageForTrace,
		isProcessing
	} from '$lib/stores/chat';

	let expandedSections = $state<Record<string, boolean>>({});

	function toggleSection(section: string) {
		expandedSections = { ...expandedSections, [section]: !expandedSections[section] };
	}

	// Reactive data from store
	let trace = $derived($displayedAgentTrace);
	let isVisible = $derived($showAgentActivity);
	let isViewingHistory = $derived($selectedMessageId !== null);
	let isStreaming = $derived($isProcessing);
	let hasContent = $derived(trace.agentTimeline.length > 0 || trace.routingDecision !== null);

	function handleClearSelection() {
		selectMessageForTrace(null);
	}
</script>

{#if isVisible}
	<aside class="w-80 bg-surface-900 border-l border-surface-800 flex flex-col overflow-hidden">
		<!-- Header -->
		<div class="p-4 border-b border-surface-800 flex items-center justify-between">
			<div class="flex items-center gap-2 flex-1 min-w-0">
				<svg
					class="w-4 h-4 flex-shrink-0 {isViewingHistory ? 'text-violet-400' : 'text-primary-light'}"
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
					stroke-width="2"
				>
					{#if isViewingHistory}
						<path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
					{:else}
						<path stroke-linecap="round" stroke-linejoin="round" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
					{/if}
				</svg>
				<div class="flex flex-col min-w-0">
					<span class="text-[11px] font-bold font-mono text-surface-400 uppercase tracking-[0.15em]">
						{isViewingHistory ? 'Saved Trace' : 'Agent Pipeline'}
					</span>
					{#if isViewingHistory}
						<span class="text-[9px] font-mono text-violet-400 truncate">Click message to view its trace</span>
					{:else if isStreaming}
						<span class="text-[9px] text-primary-light animate-pulse">Live</span>
					{/if}
				</div>
			</div>
			<div class="flex items-center gap-1">
				{#if isViewingHistory}
					<Button
						variant="link"
						size="xs"
						onclick={handleClearSelection}
						ariaLabel="Show live trace"
					>
						Live
					</Button>
				{/if}
				<IconButton
					variant="ghost"
					size="sm"
					onclick={toggleAgentActivity}
					ariaLabel="Close agent activity"
					title="Close"
				>
					<Icon name="close" size="sm" strokeWidth={2} />
				</IconButton>
			</div>
		</div>

		<!-- Content -->
		<div class="flex-1 overflow-y-auto p-4 space-y-4">
			{#if !hasContent}
				<div class="text-center py-8 text-surface-500 text-sm">
					<svg class="w-10 h-10 mx-auto mb-3 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
						<path stroke-linecap="round" stroke-linejoin="round" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
					</svg>
					{#if isViewingHistory}
						<p class="font-mono">No trace data saved</p>
						<p class="text-xs text-surface-600 mt-1 font-mono">Older messages may not have trace data</p>
					{:else}
						<p class="font-mono">No agent activity yet</p>
						<p class="text-xs text-surface-600 mt-1 font-mono">Send a message to see the pipeline</p>
					{/if}
				</div>
			{:else}
				<!-- Agent Timeline -->
				<div class="space-y-2">
					{#each trace.agentTimeline as activity}
						<AgentTimelineItem
							{activity}
							expanded={expandedSections[activity.agent] ?? false}
							onToggle={() => toggleSection(activity.agent)}
							compact
						/>
					{/each}
				</div>

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
						expanded={expandedSections['retrieval'] ?? false}
						onToggle={() => toggleSection('retrieval')}
						maxItems={5}
						compact
					/>
				{/if}

				<!-- Web Search Results -->
				{#if trace.webSearchResults}
					<WebResultsList
						results={trace.webSearchResults}
						expanded={expandedSections['web_search'] ?? false}
						onToggle={() => toggleSection('web_search')}
						maxItems={5}
						compact
					/>
				{/if}

				<!-- Validation Results (inline since it's simple) -->
				{#if trace.validationResults}
					<div class="space-y-2">
						<Button
							variant="ghost"
							size="xs"
							class="w-full justify-start gap-2 px-0 py-0 text-[10px] font-semibold text-surface-500 uppercase tracking-wider hover:text-surface-400 hover:bg-transparent"
							onclick={() => toggleSection('validation')}
						>
							<svg
								class="w-2.5 h-2.5 transition-transform {expandedSections['validation'] ? 'rotate-90' : ''}"
								fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"
							>
								<path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
							</svg>
							Validation
						</Button>

					{#if expandedSections['validation']}
						<div class="bg-surface-800/40 rounded-lg border border-surface-700/20 p-3">
							<div class="flex items-center gap-4 text-xs">
								<div>
									<span class="text-surface-500">Validated</span>
									<span class="block font-mono text-surface-300">{trace.validationResults.validated}</span>
								</div>
								<div>
									<span class="text-surface-500">Filtered</span>
									<span class="block font-mono text-surface-400">{trace.validationResults.filtered}</span>
								</div>
							</div>
						</div>
					{/if}
					</div>
				{/if}
			{/if}
		</div>

		<!-- Footer info -->
		<div class="p-3 border-t border-surface-800 bg-surface-900/50">
			<p class="text-[10px] text-surface-600 text-center font-mono">
				Agent pipeline shows the AI reasoning process
			</p>
		</div>
	</aside>
{/if}
