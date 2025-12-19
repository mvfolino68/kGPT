<script lang="ts">
	import { Card } from '$lib/components/ui';
	import type { TopicInfo } from './types';
	import OperationHeader from './OperationHeader.svelte';
	import DataTable from './DataTable.svelte';

	interface Props {
		topics: (string | TopicInfo)[];
		totalCount?: number;
	}

	let { topics, totalCount }: Props = $props();

	const displayTopics = $derived(topics.slice(0, 20));
	const count = $derived(totalCount || topics.length);
</script>

<Card>
	<OperationHeader
		icon="list"
		title="Topics"
		subtitle="{count} total"
		color="green"
	/>

	{#if topics.length > 0}
		<DataTable headers={['Topic Name', 'Partitions']} maxRows={20} totalCount={topics.length}>
			{#each displayTopics as topic}
				<tr class="border-b border-surface-700/20 last:border-b-0 hover:bg-surface-800/40 transition-colors">
					<td class="px-3 py-2 text-emerald-400">
						{typeof topic === 'string' ? topic : topic.name}
					</td>
					<td class="px-3 py-2 text-right text-surface-300">
						{typeof topic === 'object' && topic.partitions ? topic.partitions : '-'}
					</td>
				</tr>
			{/each}
		</DataTable>
	{:else}
		<p class="text-sm text-surface-400">No topics found in the cluster.</p>
	{/if}
</Card>
