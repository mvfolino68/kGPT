<script lang="ts">
	import { Button, Badge } from '$lib/components/ui';
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

	const agentConfig: Record<string, { label: string; icon: string; color: string }> = {
		router: { label: 'Router', icon: 'M13 10V3L4 14h7v7l9-11h-7z', color: 'text-violet-400' },
		retrieval: { label: 'Retrieval', icon: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z', color: 'text-blue-400' },
		kafka: { label: 'Kafka', icon: 'M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2', color: 'text-blue-400' },
		admin: { label: 'Admin', icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z', color: 'text-amber-400' },
		web_search: { label: 'Web Search', icon: 'M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9', color: 'text-green-400' },
		validation: { label: 'Validation', icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z', color: 'text-cyan-400' },
		synthesis: { label: 'Synthesis', icon: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z', color: 'text-cyan-400' },
		error: { label: 'Error', icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z', color: 'text-red-400' }
	};

	function getStatusColor(status: string): string {
		switch (status) {
			case 'started': return 'bg-amber-500';
			case 'completed': return 'bg-emerald-500';
			case 'error': return 'bg-red-500';
			default: return 'bg-surface-600';
		}
	}

	function formatDuration(ms: number | undefined): string {
		if (!ms) return '';
		if (ms < 1000) return `${ms}ms`;
		return `${(ms / 1000).toFixed(1)}s`;
	}

	let expandedSections = $state<Record<string, boolean>>({});

	function toggleSection(section: string) {
		expandedSections = { ...expandedSections, [section]: !expandedSections[section] };
	}

	let trace = $derived($displayedAgentTrace);
	let isViewingHistory = $derived($selectedMessageId !== null);
	let isStreaming = $derived($isProcessing);

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
		{#if trace.agentTimeline.length === 0 && !trace.routingDecision}
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
					{@const config = agentConfig[activity.agent] || agentConfig.error}
					<div class="card">
						<button
							type="button"
							onclick={() => activity.result && toggleSection(activity.agent)}
							class="w-full p-3 flex items-center gap-3 {activity.result ? 'cursor-pointer' : 'cursor-default'}"
						>
							<div class="w-2 h-2 rounded-full {getStatusColor(activity.status)} flex-shrink-0"></div>
							<svg class="w-4 h-4 {config.color} flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
								<path stroke-linecap="round" stroke-linejoin="round" d={config.icon} />
							</svg>
							<span class="text-sm font-medium text-surface-200 flex-1 text-left">{config.label}</span>
							{#if activity.duration_ms}
								<span class="text-xs text-surface-500 font-mono">{formatDuration(activity.duration_ms)}</span>
							{/if}
							{#if activity.result}
								<svg class="w-4 h-4 text-surface-500 transition-transform {expandedSections[activity.agent] ? 'rotate-90' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
									<path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
								</svg>
							{/if}
						</button>
						{#if expandedSections[activity.agent] && activity.result}
							<div class="px-3 pb-3 border-t border-surface-700/50">
								<pre class="text-xs text-surface-400 overflow-x-auto whitespace-pre-wrap mt-2 p-2 bg-surface-800/50 rounded">{JSON.stringify(activity.result, null, 2)}</pre>
							</div>
						{/if}
					</div>
				{/each}

				<!-- Routing Decision -->
				{#if trace.routingDecision}
					<div class="pt-2">
						<button
							type="button"
							onclick={() => toggleSection('routing')}
							class="flex items-center gap-2 text-xs font-medium text-surface-400 uppercase tracking-wider mb-2"
						>
							<svg class="w-3 h-3 transition-transform {expandedSections['routing'] ? 'rotate-90' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
								<path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
							</svg>
							Routing Decision
						</button>
						{#if expandedSections['routing']}
							<div class="card p-3 space-y-3">
								<div class="flex items-center justify-between">
									<span class="text-xs text-surface-500">Route</span>
									<Badge variant="primary">{trace.routingDecision.route}</Badge>
								</div>
								{#if trace.routingDecision.reasoning}
									<div>
										<span class="text-xs text-surface-500 block mb-1">Reasoning</span>
										<p class="text-sm text-surface-300">{trace.routingDecision.reasoning}</p>
									</div>
								{/if}
								<div class="flex flex-wrap gap-1.5">
									{#if trace.routingDecision.needs_cluster}
										<Badge variant="default">cluster</Badge>
									{/if}
									{#if trace.routingDecision.needs_retrieval}
										<Badge variant="default">retrieval</Badge>
									{/if}
									{#if trace.routingDecision.needs_web_search}
										<Badge variant="default">web search</Badge>
									{/if}
									{#if trace.routingDecision.needs_admin}
										<Badge variant="warning">admin</Badge>
									{/if}
								</div>
							</div>
						{/if}
					</div>
				{/if}

				<!-- Retrieval Results -->
				{#if trace.retrievalResults && trace.retrievalResults.docs.length > 0}
					<div class="pt-2">
						<button
							type="button"
							onclick={() => toggleSection('retrieval_results')}
							class="flex items-center gap-2 text-xs font-medium text-surface-400 uppercase tracking-wider mb-2"
						>
							<svg class="w-3 h-3 transition-transform {expandedSections['retrieval_results'] ? 'rotate-90' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
								<path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
							</svg>
							Retrieved Documents ({trace.retrievalResults.total})
						</button>
						{#if expandedSections['retrieval_results']}
							<div class="space-y-2">
								{#each trace.retrievalResults.docs.slice(0, 5) as doc}
									<div class="card p-2">
										<div class="flex items-center justify-between mb-1">
											<span class="text-xs text-surface-400 truncate max-w-[180px]">{doc.source_name}</span>
											<span class="text-xs font-mono text-emerald-400">{Math.round(doc.similarity_score * 100)}%</span>
										</div>
										<p class="text-xs text-surface-500 line-clamp-2">{doc.content_preview}</p>
									</div>
								{/each}
							</div>
						{/if}
					</div>
				{/if}

				<!-- Web Search Results -->
				{#if trace.webSearchResults && trace.webSearchResults.results.length > 0}
					<div class="pt-2">
						<button
							type="button"
							onclick={() => toggleSection('web_results')}
							class="flex items-center gap-2 text-xs font-medium text-surface-400 uppercase tracking-wider mb-2"
						>
							<svg class="w-3 h-3 transition-transform {expandedSections['web_results'] ? 'rotate-90' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
								<path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
							</svg>
							Web Results ({trace.webSearchResults.total})
						</button>
						{#if expandedSections['web_results']}
							<div class="space-y-2">
								{#each trace.webSearchResults.results.slice(0, 5) as result}
									<a
										href={result.url}
										target="_blank"
										rel="noopener noreferrer"
										class="block card p-2 hover:border-primary/30 transition-colors"
									>
										<span class="text-xs font-medium text-blue-400 truncate block">{result.title}</span>
										<span class="text-xs text-surface-500 truncate block">{result.url}</span>
									</a>
								{/each}
							</div>
						{/if}
					</div>
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

<style>
	.line-clamp-2 {
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
</style>
