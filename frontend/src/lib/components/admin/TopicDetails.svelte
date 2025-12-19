<script lang="ts">
	import { Card } from '$lib/components/ui';
	import { isPartitionDetailList, type PartitionDetail, type ConfigEntry } from './types';
	import OperationHeader from './OperationHeader.svelte';
	import DataTable from './DataTable.svelte';
	import ConfigList from './ConfigList.svelte';

	interface Props {
		topic: string;
		partitionCount?: number;
		replicationFactor?: number;
		partitions?: number | PartitionDetail[];
		config?: Record<string, ConfigEntry>;
	}

	let { topic, partitionCount, replicationFactor, partitions, config }: Props = $props();

	const partitionList = $derived(isPartitionDetailList(partitions) ? partitions : []);
	const displayPartitionCount = $derived(
		partitionCount || (isPartitionDetailList(partitions) ? partitions.length : partitions) || 0
	);
</script>

<Card>
	<OperationHeader
		icon="topic"
		title="Topic: {topic}"
		subtitle="{displayPartitionCount} partitions, RF: {replicationFactor || '?'}"
		color="green"
	/>

	{#if partitionList.length > 0}
		<div class="mb-4">
			<h4 class="text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-2">
				Partitions
			</h4>
			<DataTable headers={['Partition', 'Leader', 'Replicas', 'ISRs']}>
				{#each partitionList as partition}
					<tr class="border-b border-surface-700/20 last:border-b-0 hover:bg-surface-800/40 transition-colors">
						<td class="px-3 py-2 text-emerald-400">{partition.partition}</td>
						<td class="px-3 py-2 text-surface-300">{partition.leader ?? '-'}</td>
						<td class="px-3 py-2 text-surface-300">{partition.replicas?.join(', ') || '-'}</td>
						<td class="px-3 py-2 text-surface-300">{partition.isrs?.join(', ') || '-'}</td>
					</tr>
				{/each}
			</DataTable>
		</div>
	{/if}

	{#if config}
		<ConfigList {config} color="green" />
	{/if}
</Card>
