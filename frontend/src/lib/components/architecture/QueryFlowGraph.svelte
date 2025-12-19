<script lang="ts">
	import type { AgentGraphInfo, AgentGraphNode } from '$lib/api';
	import { Card } from '$lib/components';
	import type { ExecutionPath } from './types';
	import { nodeInfo, getPathColor } from './types';
	import AgentNode from './AgentNode.svelte';
	import ParallelNodes from './ParallelNodes.svelte';
	import FlowArrow from './FlowArrow.svelte';

	interface Props {
		agentGraph: AgentGraphInfo;
		selectedPath: ExecutionPath;
		selectedNode: string | null;
		onNodeSelect: (nodeName: string | null) => void;
	}

	let { agentGraph, selectedPath, selectedNode, onNodeSelect }: Props = $props();

	function getNodeById(name: string): AgentGraphNode | undefined {
		return agentGraph.nodes.find((n) => n.name === name);
	}

	function isNodeActive(nodeName: string): boolean {
		return selectedPath.nodes.includes(nodeName);
	}

	function toggleNode(nodeName: string) {
		onNodeSelect(selectedNode === nodeName ? null : nodeName);
	}
</script>

<Card
	title="Query flow"
	subtitle="Click any agent to see what it does"
	padding="none"
>
	<div class="p-4 sm:p-6">
		<div class="flex items-center justify-center gap-3 mb-6">
			<div class="w-2 h-2 rounded-full {getPathColor(selectedPath.color, 'bg')} animate-pulse"></div>
			<span class="text-xs text-text-tertiary">Selected path: <span class="{getPathColor(selectedPath.color, 'text')} font-medium">{selectedPath.shortName}</span></span>
		</div>

		<!-- Vertical Flow -->
		<div class="flex flex-col items-center gap-2">
			<!-- START -->
			<div class="px-4 py-1.5 bg-bg-elevated border border-white/10 rounded-lg text-xs font-medium text-text-tertiary">
				START
			</div>

			<FlowArrow pathColor="surface" isActive={false} />

			<!-- Agent Nodes -->
			{#each selectedPath.nodes as nodeName, index}
				{@const node = getNodeById(nodeName)}
				{@const info = nodeInfo[nodeName]}
				{@const isActive = isNodeActive(nodeName)}
				{@const pathColor = selectedPath.color}
				{@const hasParallel = nodeName === 'retrieval' && selectedPath.parallelNodes?.includes('web_search')}

				{#if node}
					{#if hasParallel}
						<ParallelNodes
							retrievalNode={node}
							retrievalInfo={info}
							webSearchInfo={nodeInfo['web_search']}
							{pathColor}
							{selectedNode}
							stepNumber={index + 1}
							onSelectRetrieval={() => toggleNode('retrieval')}
							onSelectWebSearch={() => toggleNode('web_search')}
						/>
					{:else}
						<AgentNode
							{node}
							{info}
							{isActive}
							isSelected={selectedNode === nodeName}
							{pathColor}
							stepNumber={index + 1}
							onToggle={() => toggleNode(nodeName)}
						/>
					{/if}

					{#if index < selectedPath.nodes.length - 1}
						<FlowArrow {pathColor} {isActive} />
					{/if}
				{/if}
			{/each}

			<FlowArrow pathColor={selectedPath.color} />

			<!-- END -->
			<div class="px-4 py-1.5 bg-bg-elevated border border-white/10 rounded-lg text-xs font-medium text-text-tertiary">
				END
			</div>
		</div>

		<!-- Hint -->
		<div class="mt-8 text-center">
			<p class="text-xs text-text-tertiary">{selectedPath.hint}</p>
		</div>
	</div>
</Card>
