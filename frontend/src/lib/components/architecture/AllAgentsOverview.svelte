<script lang="ts">
	import type { AgentGraphNode } from '$lib/api';
	import { Card } from '$lib/components';
	import { nodeInfo, getNodeColor } from './types';
	import OverviewTile from './OverviewTile.svelte';

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
			<OverviewTile
				title={node.label}
				subtitle={node.name}
				description={info?.role || node.description}
				tone={{ bg: 'bg-bg-elevated', text: nodeColor }}
				iconPath={node.icon}
			/>
		{/each}

		<!-- Web Search Agent (Exa) -->
		<OverviewTile
			title="Exa Search"
			subtitle="web_search"
			description={nodeInfo['web_search']?.role || 'Real-time web search via Exa API'}
			tone={{ bg: 'bg-primary/10', text: 'text-primary' }}
			iconPath="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"
		/>
	</div>
</Card>
