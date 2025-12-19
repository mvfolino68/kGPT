<script lang="ts">
	import type { WebSearchResults } from '$lib/stores/chat';

	interface Props {
		results: WebSearchResults;
		expanded: boolean;
		onToggle: () => void;
		maxItems?: number;
		compact?: boolean;
	}

	let { results, expanded, onToggle, maxItems = 5, compact = false }: Props = $props();

	const items = $derived(results.results.slice(0, maxItems));
</script>

{#if results.results.length > 0}
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
			Web ({results.total})
		</button>

		{#if expanded}
			<div class="space-y-1.5">
				{#each items as result}
					<a
						href={result.url}
						target="_blank"
						rel="noopener noreferrer"
						class="block rounded bg-surface-700/50 p-2 hover:bg-surface-700/70 transition-colors"
					>
						<span class="font-medium text-blue-400 truncate block {compact ? 'text-[10px]' : 'text-xs'}">
							{result.title}
						</span>
						<span class="text-surface-500 truncate block {compact ? 'text-[9px]' : 'text-xs'}">
							{result.url}
						</span>
					</a>
				{/each}
			</div>
		{/if}
	</div>
{/if}
