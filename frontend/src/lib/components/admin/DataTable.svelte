<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		headers: string[];
		maxRows?: number;
		totalCount?: number;
		children: Snippet;
	}

	let { headers, maxRows = 20, totalCount, children }: Props = $props();

	const showMore = $derived(totalCount && totalCount > maxRows);
</script>

<div class="bg-surface-800/30 rounded-lg overflow-hidden">
	<table class="w-full text-xs">
		<thead>
			<tr class="border-b border-surface-700/30 bg-surface-800/50">
				{#each headers as header, i}
					<th class="px-3 py-2 text-surface-500 font-medium {i === headers.length - 1 ? 'text-right' : 'text-left'}">
						{header}
					</th>
				{/each}
			</tr>
		</thead>
		<tbody>
			{@render children()}
		</tbody>
	</table>
	{#if showMore}
		<div class="px-3 py-2 text-xs text-surface-500 bg-surface-800/30 border-t border-surface-700/30">
			... and {totalCount - maxRows} more
		</div>
	{/if}
</div>
