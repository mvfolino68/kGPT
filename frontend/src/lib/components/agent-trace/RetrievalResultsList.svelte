<script lang="ts">
	import type { RetrievalResults } from '$lib/stores/chat';

	interface Props {
		results: RetrievalResults;
		expanded: boolean;
		onToggle: () => void;
		maxItems?: number;
		compact?: boolean;
	}

	let { results, expanded, onToggle, maxItems = 5, compact = false }: Props = $props();

	const docs = $derived(results.docs.slice(0, maxItems));
</script>

{#if results.docs.length > 0}
	<div class="pt-2 mt-2">
		<button
			type="button"
			onclick={onToggle}
			class="flex items-center gap-1.5 font-medium text-surface-500 uppercase tracking-wider mb-2 hover:text-surface-400
				{compact ? 'text-[10px]' : 'text-xs'}"
		>
			<svg
				class="transition-transform {compact ? 'w-2.5 h-2.5' : 'w-3 h-3'} {expanded ? 'rotate-90' : ''}"
				fill="none"
				stroke="currentColor"
				viewBox="0 0 24 24"
				stroke-width="2"
			>
				<path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
			</svg>
			Documents ({results.total})
		</button>

		{#if expanded}
			<div class="space-y-1.5">
				{#each docs as doc}
					<div class="rounded bg-surface-700/50 p-2">
						<div class="flex items-center justify-between mb-1">
							<span
								class="text-surface-400 truncate {compact ? 'max-w-[140px] text-[10px]' : 'max-w-[180px] text-xs'}"
							>
								{doc.source_name}
							</span>
							<span class="font-mono text-emerald-400 {compact ? 'text-[10px]' : 'text-xs'}">
								{Math.round(doc.similarity_score * 100)}%
							</span>
						</div>
						<p class="text-surface-500 line-clamp-2 {compact ? 'text-[10px]' : 'text-xs'}">
							{doc.content_preview}
						</p>
					</div>
				{/each}
			</div>
		{/if}
	</div>
{/if}

<style>
	.line-clamp-2 {
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
</style>
