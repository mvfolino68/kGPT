<script lang="ts">
	import {
		currentAgentTrace,
		showAgentActivity,
		toggleAgentActivity,
		type AgentActivity,
		type RoutingDecision,
		type RetrievalResults,
		type ValidationResults
	} from '$lib/stores/chat';

	// Agent display configuration
	const agentConfig: Record<string, { label: string; icon: string; color: string }> = {
		router: { label: 'Router', icon: 'M13 10V3L4 14h7v7l9-11h-7z', color: 'text-violet-400' },
		retrieval: { label: 'Retrieval', icon: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z', color: 'text-blue-400' },
		kafka: { label: 'Kafka', icon: 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10', color: 'text-emerald-400' },
		admin: { label: 'Admin', icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z', color: 'text-amber-400' },
		validation: { label: 'Validation', icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z', color: 'text-cyan-400' },
		synthesis: { label: 'Synthesis', icon: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z', color: 'text-emerald-400' },
		error: { label: 'Error', icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z', color: 'text-red-400' }
	};

	function getStatusIndicator(status: string): { bg: string; animate: boolean } {
		switch (status) {
			case 'started':
				return { bg: 'bg-amber-400', animate: true };
			case 'completed':
				return { bg: 'bg-emerald-400', animate: false };
			case 'error':
				return { bg: 'bg-red-400', animate: false };
			default:
				return { bg: 'bg-surface-600', animate: false };
		}
	}

	function formatDuration(ms: number | undefined): string {
		if (!ms) return '';
		if (ms < 1000) return `${ms}ms`;
		return `${(ms / 1000).toFixed(1)}s`;
	}

	let expandedSections = $state<Record<string, boolean>>({});

	function toggleSection(section: string) {
		expandedSections[section] = !expandedSections[section];
	}

	// Reactive data from store
	let trace = $derived($currentAgentTrace);
	let isVisible = $derived($showAgentActivity);
</script>

{#if isVisible}
	<aside class="w-80 bg-surface-900/70 backdrop-blur-xl border-l retro-border flex flex-col overflow-hidden">
		<!-- Header -->
		<div class="p-4 border-b retro-border flex items-center justify-between">
			<div class="flex items-center gap-2">
				<svg class="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
				</svg>
				<span class="text-[11px] font-bold font-mono text-surface-400 uppercase tracking-[0.15em]">Agent Pipeline</span>
			</div>
			<button
				type="button"
				onclick={toggleAgentActivity}
				class="retro-button px-1.5 py-1 text-surface-500 hover:text-surface-300"
				aria-label="Close agent activity"
			>
				<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</button>
		</div>

		<!-- Content -->
		<div class="flex-1 overflow-y-auto p-4 space-y-4">
			{#if trace.agentTimeline.length === 0}
				<div class="text-center py-8 text-surface-500 text-sm">
					<svg class="w-10 h-10 mx-auto mb-3 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
						<path stroke-linecap="round" stroke-linejoin="round" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
					</svg>
					<p class="font-mono">No agent activity yet</p>
					<p class="text-xs text-surface-600 mt-1 font-mono">Send a message to see the pipeline</p>
				</div>
			{:else}
				<!-- Agent Timeline -->
				<div class="space-y-2">
					{#each trace.agentTimeline as activity}
						{@const config = agentConfig[activity.agent] || agentConfig.error}
						{@const statusIndicator = getStatusIndicator(activity.status)}
						<div class="retro-card rounded-lg overflow-hidden hover:bg-surface-800/60 transition-colors">
							<button
								type="button"
								onclick={() => toggleSection(activity.agent)}
								class="w-full px-3 py-2.5 flex items-center gap-3"
							>
								<!-- Status indicator with LED -->
								<div class="relative">
									<div class="w-2 h-2 rounded-full {statusIndicator.bg} {statusIndicator.animate ? 'animate-glow-pulse' : ''}"></div>
								</div>

								<!-- Agent icon and name -->
								<div class="flex items-center gap-2 flex-1 min-w-0">
									<svg class="w-4 h-4 {config.color} flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
										<path stroke-linecap="round" stroke-linejoin="round" d={config.icon} />
									</svg>
									<span class="text-sm font-mono text-surface-200 truncate">{config.label}</span>
								</div>

								<!-- Duration -->
								{#if activity.duration_ms}
									<span class="text-xs font-mono text-surface-500 tabular-nums">{formatDuration(activity.duration_ms)}</span>
								{/if}

								<!-- Expand/collapse icon -->
								{#if activity.result}
									<svg
										class="w-4 h-4 text-surface-500 transition-transform {expandedSections[activity.agent] ? 'rotate-90' : ''}"
										fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"
									>
										<path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
									</svg>
								{/if}
							</button>

							<!-- Expanded details -->
							{#if expandedSections[activity.agent] && activity.result}
								<div class="px-3 pb-3 border-t retro-border mt-1 pt-2 bg-surface-900/50">
									<pre class="text-xs font-mono text-surface-400 overflow-x-auto whitespace-pre-wrap break-all">{JSON.stringify(activity.result, null, 2)}</pre>
								</div>
							{/if}
						</div>
					{/each}
				</div>

				<!-- Routing Decision -->
				{#if trace.routingDecision}
					<div class="space-y-2">
						<button
							type="button"
							onclick={() => toggleSection('routing')}
							class="w-full flex items-center gap-2 text-xs font-semibold text-surface-500 uppercase tracking-wider hover:text-surface-400 transition-colors"
						>
							<svg
								class="w-3 h-3 transition-transform {expandedSections['routing'] ? 'rotate-90' : ''}"
								fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"
							>
								<path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
							</svg>
							Routing Decision
						</button>

						{#if expandedSections['routing']}
							<div class="bg-surface-800/60 rounded-lg border border-violet-500/20 p-3 space-y-2">
								<div class="flex items-center justify-between">
									<span class="text-xs text-surface-500">Route</span>
									<span class="text-sm font-mono text-violet-400">{trace.routingDecision.route}</span>
								</div>
								{#if trace.routingDecision.reasoning}
									<div>
										<span class="text-xs text-surface-500 block mb-1">Reasoning</span>
										<p class="text-sm text-surface-300">{trace.routingDecision.reasoning}</p>
									</div>
								{/if}
								{#if trace.routingDecision.sub_goals.length > 0}
									<div>
										<span class="text-xs text-surface-500 block mb-1">Sub-goals</span>
										<ul class="space-y-1">
											{#each trace.routingDecision.sub_goals as goal}
												<li class="text-xs text-surface-400 flex items-start gap-1.5">
													<span class="text-violet-400 mt-0.5">-</span>
													{goal}
												</li>
											{/each}
										</ul>
									</div>
								{/if}
								<div class="flex flex-wrap gap-2 pt-1">
									{#if trace.routingDecision.needs_cluster}
										<span class="px-2 py-0.5 text-xs rounded bg-emerald-500/20 text-emerald-400">cluster</span>
									{/if}
									{#if trace.routingDecision.needs_retrieval}
										<span class="px-2 py-0.5 text-xs rounded bg-blue-500/20 text-blue-400">retrieval</span>
									{/if}
									{#if trace.routingDecision.needs_admin}
										<span class="px-2 py-0.5 text-xs rounded bg-amber-500/20 text-amber-400">admin</span>
									{/if}
								</div>
							</div>
						{/if}
					</div>
				{/if}

				<!-- Retrieval Results -->
				{#if trace.retrievalResults}
					<div class="space-y-2">
						<button
							type="button"
							onclick={() => toggleSection('retrieval')}
							class="w-full flex items-center gap-2 text-xs font-semibold text-surface-500 uppercase tracking-wider hover:text-surface-400 transition-colors"
						>
							<svg
								class="w-3 h-3 transition-transform {expandedSections['retrieval'] ? 'rotate-90' : ''}"
								fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"
							>
								<path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
							</svg>
							Retrieval ({trace.retrievalResults.total} docs)
						</button>

						{#if expandedSections['retrieval']}
							<div class="bg-surface-800/60 rounded-lg border border-blue-500/20 p-3 space-y-3">
								<div class="grid grid-cols-2 gap-2 text-xs">
									<div>
										<span class="text-surface-500">Queries expanded</span>
										<span class="block font-mono text-blue-400">{trace.retrievalResults.queries_expanded}</span>
									</div>
									<div>
										<span class="text-surface-500">Reranked</span>
										<span class="block font-mono {trace.retrievalResults.reranked ? 'text-emerald-400' : 'text-surface-400'}">
											{trace.retrievalResults.reranked ? 'Yes' : 'No'}
										</span>
									</div>
								</div>

								{#if trace.retrievalResults.docs.length > 0}
									<div class="space-y-2 max-h-48 overflow-y-auto">
										{#each trace.retrievalResults.docs.slice(0, 5) as doc, i}
											<div class="text-xs bg-surface-900/60 rounded p-2 border border-white/5">
												<div class="flex items-center justify-between mb-1">
													<span class="text-surface-400 truncate max-w-[140px]">{doc.source_name}</span>
													<span class="font-mono text-emerald-400">{(doc.similarity_score * 100).toFixed(0)}%</span>
												</div>
												<p class="text-surface-500 line-clamp-2">{doc.content_preview}</p>
											</div>
										{/each}
									</div>
								{/if}
							</div>
						{/if}
					</div>
				{/if}

				<!-- Validation Results -->
				{#if trace.validationResults}
					<div class="space-y-2">
						<button
							type="button"
							onclick={() => toggleSection('validation')}
							class="w-full flex items-center gap-2 text-xs font-semibold text-surface-500 uppercase tracking-wider hover:text-surface-400 transition-colors"
						>
							<svg
								class="w-3 h-3 transition-transform {expandedSections['validation'] ? 'rotate-90' : ''}"
								fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"
							>
								<path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
							</svg>
							Validation
						</button>

						{#if expandedSections['validation']}
							<div class="bg-surface-800/60 rounded-lg border border-cyan-500/20 p-3">
								<div class="flex items-center gap-4 text-xs">
									<div>
										<span class="text-surface-500">Validated</span>
										<span class="block font-mono text-emerald-400">{trace.validationResults.validated}</span>
									</div>
									<div>
										<span class="text-surface-500">Filtered</span>
										<span class="block font-mono text-amber-400">{trace.validationResults.filtered}</span>
									</div>
								</div>
							</div>
						{/if}
					</div>
				{/if}
			{/if}
		</div>

		<!-- Footer info -->
		<div class="p-3 border-t retro-border bg-surface-900/50">
			<p class="text-[10px] text-surface-600 text-center font-mono">
				Agent pipeline shows the AI reasoning process
			</p>
		</div>
	</aside>
{/if}

<style>
	.line-clamp-2 {
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
</style>

