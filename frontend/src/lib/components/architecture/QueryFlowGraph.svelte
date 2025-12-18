<script lang="ts">
	import type { AgentGraphInfo, AgentGraphNode } from '$lib/api';
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

<div class="bg-surface-900 border border-surface-700/50 rounded-lg overflow-hidden">
	<div class="px-6 py-4 border-b border-surface-700/50">
		<div class="flex items-center justify-between">
			<div class="flex items-center gap-3">
				<div class="w-2 h-2 rounded-full {getPathColor(selectedPath.color, 'bg')} {getPathColor(selectedPath.color, 'border')} border animate-pulse"></div>
				<span class="text-sm text-surface-200">Query Flow</span>
			</div>
			<span class="text-xs text-surface-500">Click any agent for details</span>
		</div>
	</div>

	<div class="p-8">
		<!-- Vertical Flow -->
		<div class="flex flex-col items-center gap-2">
			<!-- START -->
			<div class="px-5 py-2 bg-surface-800 border border-surface-700/50 rounded-lg text-sm text-surface-400">
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
			<div class="px-5 py-2 rounded-lg text-sm {getPathColor(selectedPath.color, 'bg')} {getPathColor(selectedPath.color, 'text')} border {getPathColor(selectedPath.color, 'border')}">
				END
			</div>
		</div>

		<!-- Hint -->
		<div class="mt-8 text-center">
			<p class="text-xs text-surface-500">{selectedPath.hint}</p>
		</div>
	</div>
</div>
