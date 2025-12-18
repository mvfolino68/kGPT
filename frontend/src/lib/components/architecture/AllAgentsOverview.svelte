<script lang="ts">
	import type { AgentGraphNode } from '$lib/api';
	import { nodeInfo } from './types';

	interface Props {
		nodes: AgentGraphNode[];
	}

	let { nodes }: Props = $props();
</script>

<div class="bg-surface-900 border border-surface-700/50 rounded-lg overflow-hidden">
	<div class="px-6 py-4 border-b border-surface-700/50">
		<h2 class="text-sm text-surface-200">All Agents</h2>
		<p class="text-xs text-surface-500 mt-1">
			The 6 specialized agents that power kGPT
		</p>
	</div>

	<div class="p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
		{#each nodes as node}
			{@const info = nodeInfo[node.name]}
			<div class="p-4 bg-surface-800/50 rounded-xl border border-surface-700/50 hover:border-surface-600 transition-colors">
				<div class="flex items-center gap-3 mb-3">
					<div class="w-10 h-10 rounded-lg bg-surface-800 flex items-center justify-center">
						<svg class="w-5 h-5 {node.color}" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d={node.icon} />
						</svg>
					</div>
					<div>
						<div class="text-sm font-bold {node.color}">{node.label}</div>
						<div class="text-xs text-surface-500">{node.name}</div>
					</div>
				</div>
				<p class="text-xs text-surface-400">{info?.role || node.description}</p>
			</div>
		{/each}

		<!-- Web Search Agent (Exa) -->
		<div class="p-4 bg-surface-800/50 rounded-xl border border-surface-700/50 hover:border-primary/50 transition-colors">
			<div class="flex items-center gap-3 mb-3">
				<div class="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
					<svg class="w-5 h-5 text-primary-light" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
					</svg>
				</div>
				<div>
					<div class="text-sm font-bold text-primary-light">Exa Search</div>
					<div class="text-xs text-surface-500">web_search</div>
				</div>
			</div>
			<p class="text-xs text-surface-400">{nodeInfo['web_search']?.role || 'Real-time web search via Exa API'}</p>
		</div>
	</div>
</div>
