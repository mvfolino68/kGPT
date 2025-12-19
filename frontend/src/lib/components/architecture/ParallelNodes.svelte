<script lang="ts">
	import type { AgentGraphNode } from '$lib/api';
	import type { NodeInfo } from './types';
	import { getPathColor } from './types';
	import { CardButton } from '$lib/components/ui';
	import PathTint from './PathTint.svelte';

	interface Props {
		retrievalNode: AgentGraphNode;
		retrievalInfo: NodeInfo | undefined;
		webSearchInfo: NodeInfo;
		pathColor: string;
		selectedNode: string | null;
		stepNumber: number;
		onSelectRetrieval: () => void;
		onSelectWebSearch: () => void;
	}

	let {
		retrievalNode,
		retrievalInfo,
		webSearchInfo,
		pathColor,
		selectedNode,
		stepNumber,
		onSelectRetrieval,
		onSelectWebSearch
	}: Props = $props();
</script>

<div class="w-full max-w-lg">
	<div class="flex items-center justify-center gap-2 mb-2">
		<div class="h-px flex-1 bg-white/10"></div>
		<span class="text-xs text-text-tertiary px-2">parallel</span>
		<div class="h-px flex-1 bg-white/10"></div>
	</div>
	<div class="flex gap-3">
		<!-- Retrieval Node -->
		<CardButton
			variant="active"
			size="md"
			selected={selectedNode === 'retrieval'}
			class="flex-1 relative overflow-hidden {getPathColor(pathColor, 'border')} {getPathColor(pathColor, 'glow')}"
			onclick={onSelectRetrieval}
		>
			<PathTint color={pathColor} opacity={0.10} roundedClass="rounded-xl" />
			<div class="relative flex items-center gap-3">
				<div class="w-10 h-10 rounded-lg flex items-center justify-center bg-bg-elevated border {getPathColor(pathColor, 'border')}">
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
				<div
					class="w-7 h-7 rounded-full flex items-center justify-center text-xs bg-bg-elevated border {getPathColor(pathColor, 'border')} {getPathColor(pathColor, 'text')}"
					aria-label={"Step " + stepNumber}
				>
					{stepNumber}
				</div>
			</div>
			{#if selectedNode === 'retrieval' && retrievalInfo}
				<div class="mt-3 pt-3 border-t border-current/20">
					<div class="space-y-1.5">
						{#each retrievalInfo.details as detail}
							<div class="text-xs text-left p-2 rounded-lg bg-bg-elevated/60">
								<span class="{getPathColor(pathColor, 'text')}">*</span>
								<span class="text-text-secondary ml-1">{detail}</span>
							</div>
						{/each}
					</div>
				</div>
			{/if}
		</CardButton>

		<!-- Web Search Node -->
		<CardButton
			variant="active"
			size="md"
			selected={selectedNode === 'web_search'}
			class="flex-1 relative overflow-hidden {getPathColor(pathColor, 'border')} {getPathColor(pathColor, 'glow')}"
			onclick={onSelectWebSearch}
		>
			<PathTint color={pathColor} opacity={0.10} roundedClass="rounded-xl" />
			<div class="relative flex items-center gap-3">
				<div class="w-10 h-10 rounded-lg flex items-center justify-center bg-bg-elevated border {getPathColor(pathColor, 'border')}">
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
				<div
					class="w-7 h-7 rounded-full flex items-center justify-center text-xs bg-bg-elevated border {getPathColor(pathColor, 'border')} {getPathColor(pathColor, 'text')}"
					aria-label={"Step " + stepNumber}
				>
					{stepNumber}
				</div>
			</div>
			{#if selectedNode === 'web_search' && webSearchInfo}
				<div class="mt-3 pt-3 border-t border-current/20">
					<div class="space-y-1.5">
						{#each webSearchInfo.details as detail}
							<div class="text-xs text-left p-2 rounded-lg bg-bg-elevated/60">
								<span class="{getPathColor(pathColor, 'text')}">*</span>
								<span class="text-text-secondary ml-1">{detail}</span>
							</div>
						{/each}
					</div>
				</div>
			{/if}
		</CardButton>
	</div>
	<div class="flex items-center justify-center gap-2 mt-2">
		<div class="h-px flex-1 bg-white/10"></div>
		<span class="text-xs text-text-tertiary px-2">merge</span>
		<div class="h-px flex-1 bg-white/10"></div>
	</div>
</div>
