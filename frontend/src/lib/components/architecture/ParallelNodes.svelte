<script lang="ts">
	import type { AgentGraphNode } from '$lib/api';
	import type { NodeInfo } from './types';
	import { getPathColor } from './types';

	interface Props {
		retrievalNode: AgentGraphNode;
		retrievalInfo: NodeInfo | undefined;
		webSearchInfo: NodeInfo;
		pathColor: string;
		selectedNode: string | null;
		onSelectRetrieval: () => void;
		onSelectWebSearch: () => void;
	}

	let { retrievalNode, retrievalInfo, webSearchInfo, pathColor, selectedNode, onSelectRetrieval, onSelectWebSearch }: Props = $props();
</script>

<div class="w-full max-w-lg">
	<div class="flex items-center justify-center gap-2 mb-2">
		<div class="h-px flex-1 bg-white/10"></div>
		<span class="text-xs text-text-tertiary px-2">parallel</span>
		<div class="h-px flex-1 bg-white/10"></div>
	</div>
	<div class="flex gap-3">
		<!-- Retrieval Node -->
		<button
			type="button"
			onclick={onSelectRetrieval}
			class="
				flex-1 p-3 rounded-xl border
				transition-all duration-150 ease-out
				focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:ring-offset-2 focus-visible:ring-offset-bg
				{getPathColor(pathColor, 'bg')} {getPathColor(pathColor, 'border')} shadow-lg {getPathColor(pathColor, 'glow')}
				{selectedNode === 'retrieval' ? 'ring-1 ring-white/10' : ''}
			"
		>
			<div class="flex items-center gap-3">
				<div class="w-10 h-10 rounded-lg flex items-center justify-center {getPathColor(pathColor, 'bg')}">
					<svg
						class="w-5 h-5 {getPathColor(pathColor, 'text')}"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
						stroke-width="2"
					>
						<path stroke-linecap="round" stroke-linejoin="round" d={retrievalNode.icon} />
					</svg>
				</div>
				<div class="flex-1 text-left">
					<div class="text-sm font-semibold {getPathColor(pathColor, 'text')}">
						{retrievalNode.label}
					</div>
					<div class="text-xs text-text-tertiary mt-0.5">Searches indexed docs</div>
				</div>
			</div>
			{#if selectedNode === 'retrieval' && retrievalInfo}
				<div class="mt-3 pt-3 border-t border-current/20">
					<div class="space-y-1">
						{#each retrievalInfo.details as detail}
							<div class="text-xs text-left text-text-secondary">* {detail}</div>
						{/each}
					</div>
				</div>
			{/if}
		</button>

		<!-- Web Search Node -->
		<button
			type="button"
			onclick={onSelectWebSearch}
			class="
				flex-1 p-3 rounded-xl border
				transition-all duration-150 ease-out
				focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:ring-offset-2 focus-visible:ring-offset-bg
				{getPathColor(pathColor, 'bg')} {getPathColor(pathColor, 'border')} shadow-lg {getPathColor(pathColor, 'glow')}
				{selectedNode === 'web_search' ? 'ring-1 ring-white/10' : ''}
			"
		>
			<div class="flex items-center gap-3">
				<div class="w-10 h-10 rounded-lg flex items-center justify-center {getPathColor(pathColor, 'bg')}">
					<svg
						class="w-5 h-5 {getPathColor(pathColor, 'text')}"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
						stroke-width="2"
					>
						<path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
					</svg>
				</div>
				<div class="flex-1 text-left">
					<div class="text-sm font-semibold {getPathColor(pathColor, 'text')}">
						Exa Search
					</div>
					<div class="text-xs text-text-tertiary mt-0.5">Real-time web search</div>
				</div>
			</div>
			{#if selectedNode === 'web_search' && webSearchInfo}
				<div class="mt-3 pt-3 border-t border-current/20">
					<div class="space-y-1">
						{#each webSearchInfo.details as detail}
							<div class="text-xs text-left text-text-secondary">* {detail}</div>
						{/each}
					</div>
				</div>
			{/if}
		</button>
	</div>
	<div class="flex items-center justify-center gap-2 mt-2">
		<div class="h-px flex-1 bg-white/10"></div>
		<span class="text-xs text-text-tertiary px-2">merge</span>
		<div class="h-px flex-1 bg-white/10"></div>
	</div>
</div>
