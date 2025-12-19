<script lang="ts">
	import type { AgentGraphNode } from '$lib/api';
	import { Card } from '$lib/components';
	import { nodeInfo, getNodeColor } from './types';

	interface Props {
		nodes: AgentGraphNode[];
	}

	let { nodes }: Props = $props();
</script>

<Card
	title="All agents"
	subtitle="The specialized agents that power kGPT"
>
	<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
		{#each nodes as node}
			{@const info = nodeInfo[node.name]}
			{@const nodeColor = getNodeColor(node.name)}
			<div class="p-4 bg-surface-700/30 rounded-xl hover:bg-surface-700/50 transition-colors cursor-pointer">
				<div class="flex items-center gap-3 mb-3">
					<div class="w-10 h-10 rounded-lg bg-bg-elevated flex items-center justify-center">
						<svg class="w-5 h-5 {nodeColor}" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d={node.icon} />
						</svg>
					</div>
					<div>
						<div class="text-sm font-bold {nodeColor}">{node.label}</div>
						<div class="text-xs text-text-tertiary">{node.name}</div>
					</div>
				</div>
				<p class="text-xs text-text-secondary">{info?.role || node.description}</p>
			</div>
		{/each}

		<!-- Web Search Agent (Exa) -->
		<div class="p-4 bg-surface-700/30 rounded-xl hover:bg-surface-700/50 transition-colors cursor-pointer">
			<div class="flex items-center gap-3 mb-3">
				<div class="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
					<svg class="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
					</svg>
				</div>
				<div>
					<div class="text-sm font-bold text-primary">Exa Search</div>
					<div class="text-xs text-text-tertiary">web_search</div>
				</div>
			</div>
			<p class="text-xs text-text-secondary">{nodeInfo['web_search']?.role || 'Real-time web search via Exa API'}</p>
		</div>
	</div>
</Card>
