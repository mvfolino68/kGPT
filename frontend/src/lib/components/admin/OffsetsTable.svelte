<script lang="ts">
	import type { OffsetInfo } from './types';
	import OperationHeader from './OperationHeader.svelte';
	import DataTable from './DataTable.svelte';

	interface Props {
		groupId: string;
		offsets: OffsetInfo[];
	}

	let { groupId, offsets }: Props = $props();

	const displayOffsets = $derived(offsets.slice(0, 20));
</script>

<div class="bg-surface-900 border border-surface-700/50 rounded-lg p-4">
	<OperationHeader
		icon="offsets"
		title="Offsets: {groupId}"
		subtitle="{offsets.length} partitions"
		color="amber"
	/>

	{#if offsets.length > 0}
		<DataTable headers={['Topic', 'Partition', 'Offset']} maxRows={20} totalCount={offsets.length}>
			{#each displayOffsets as offset}
				<tr class="border-b border-surface-700/30 last:border-b-0 hover:bg-surface-800/60 transition-colors">
					<td class="px-3 py-2 text-amber-400">{offset.topic}</td>
					<td class="px-3 py-2 text-right text-surface-300">{offset.partition}</td>
					<td class="px-3 py-2 text-right text-surface-300">{offset.offset}</td>
				</tr>
			{/each}
		</DataTable>
	{/if}
</div>
