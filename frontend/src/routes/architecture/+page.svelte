<script lang="ts">
	import { onMount } from 'svelte';
	import { getAgentGraph, type AgentGraphInfo } from '$lib/api';
	import { Header, HeaderStatus } from '$lib/components';
	import { Hint } from '$lib/components/hints';
	import {
		PathSelector,
		SelectedPathInfo,
		QueryFlowGraph,
		AllAgentsOverview,
		TechnologyStack,
		GraphStats,
		CallToAction,
		executionPaths
	} from '$lib/components/architecture';

	let agentGraph = $state<AgentGraphInfo | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);
	let selectedPath = $state<number>(0);
	let selectedNode = $state<string | null>(null);

	onMount(async () => {
		await loadGraph();
	});

	async function loadGraph() {
		loading = true;
		error = null;
		try {
			agentGraph = await getAgentGraph();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load agent graph';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Agent Architecture - kGPT</title>
</svelte:head>

<div class="flex flex-col h-full bg-surface-900">
	<Header title="Agent Architecture" subtitle="Multi-agent RAG orchestration">
		{#snippet actions()}
			<div class="flex items-center gap-4">
				<HeaderStatus status="active" label="LangGraph" pulse />
				<button type="button" class="btn btn-ghost btn-sm" onclick={loadGraph} disabled={loading}>
					{loading ? 'Loading...' : 'Refresh'}
				</button>
			</div>
		{/snippet}
	</Header>

	<div class="flex-1 overflow-y-auto p-6">
		<div class="max-w-5xl mx-auto space-y-8">
			{#if error}
				<div class="bg-red-500/5 rounded-lg p-4 flex items-center gap-3">
					<StatusIndicator status="error" />
					<span class="text-sm text-red-400">{error}</span>
					<button type="button" class="btn btn-ghost btn-sm" onclick={loadGraph}>Retry</button>
				</div>
			{:else if loading}
				<div class="flex items-center justify-center py-20">
					<div class="text-center space-y-4">
						<div class="w-12 h-12 mx-auto border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
						<p class="text-surface-400">Loading agent graph...</p>
					</div>
				</div>
			{:else if agentGraph}
				<!-- Hero -->
				<section class="text-center py-6">
					<h1 class="text-3xl font-bold text-surface-100 mb-3">
						Multi-Agent Orchestration
					</h1>
					<p class="text-surface-400 text-sm max-w-2xl mx-auto">
						Your question flows through specialized AI agents. Select a path below to see how
						different queries are handled.
					</p>
				</section>

				<!-- Path Selector -->
				<PathSelector
					{selectedPath}
					onSelect={(id) => selectedPath = id}
				/>

				<!-- Selected Path Info -->
				<SelectedPathInfo path={executionPaths[selectedPath]} />

				<!-- Interactive Graph -->
				<QueryFlowGraph
					{agentGraph}
					selectedPath={executionPaths[selectedPath]}
					{selectedNode}
					onNodeSelect={(node) => selectedNode = node}
				/>

				<!-- All Agents Overview -->
				<AllAgentsOverview nodes={agentGraph.nodes} />

				<!-- Technology Stack -->
				<TechnologyStack />

				<!-- Graph Stats -->
				<div class="bg-surface-800 rounded-lg overflow-hidden">
					<GraphStats agents={agentGraph.nodes.length + 1} edges={agentGraph.edges.length} />
				</div>

				<!-- CTA -->
				<CallToAction />
			{/if}
		</div>
	</div>
</div>

<!-- Contextual Hint -->
<Hint
	id="architecture"
	title="Explore the AI Pipeline"
	description="This visualization shows how your queries flow through specialized agents. Each agent handles a different task like routing, retrieval, or synthesis."
/>
