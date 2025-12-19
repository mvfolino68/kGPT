<script lang="ts">
	import { Button, StatusDot, Icon, Card } from '$lib/components';
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

<div class="flex flex-col h-full bg-bg">
	<Header title="Agent Architecture" subtitle="Multi-agent RAG orchestration">
		{#snippet actions()}
			<div class="flex items-center gap-4">
				<HeaderStatus status="active" label="LangGraph" pulse />
				<Button variant="ghost" size="sm" onclick={loadGraph} disabled={loading} loading={loading}>
					Refresh
				</Button>
			</div>
		{/snippet}
	</Header>

	<div class="flex-1 overflow-y-auto p-6">
		<div class="max-w-5xl mx-auto space-y-8">
			{#if error}
				<Card variant="error" padding="sm">
					<div class="flex items-center gap-2 text-sm">
						<StatusDot status="error" />
						<span class="text-error flex-1">{error}</span>
						<Button variant="ghost" size="sm" onclick={loadGraph}>Retry</Button>
					</div>
				</Card>
			{:else if loading}
				<div class="flex items-center justify-center py-20">
					<div class="text-center space-y-4">
						<Icon name="spinner" size="xl" class="mx-auto text-primary animate-spin" />
						<p class="text-text-secondary">Loading agent graph...</p>
					</div>
				</div>
			{:else if agentGraph}
				<!-- Hero -->
				<section class="text-center py-6">
					<h1 class="text-3xl font-bold text-text mb-3">
						Multi-Agent Orchestration
					</h1>
					<p class="text-text-secondary text-sm max-w-2xl mx-auto">
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
				<GraphStats agents={agentGraph.nodes.length + 1} edges={agentGraph.edges.length} />

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
