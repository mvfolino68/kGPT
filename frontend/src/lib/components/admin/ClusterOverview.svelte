<script lang="ts">
	import { Card } from '$lib/components/ui';
	import type { BrokerInfo } from './types';
	import OperationHeader from './OperationHeader.svelte';
	import DataTable from './DataTable.svelte';

	interface Props {
		clusterId?: string;
		controllerId?: number;
		brokerCount?: number;
		topicCount?: number;
		brokers?: BrokerInfo[];
	}

	let { clusterId, controllerId, brokerCount = 0, topicCount = 0, brokers = [] }: Props = $props();
</script>

<Card>
	<OperationHeader
		icon="cluster"
		title="Cluster Overview"
		subtitle="{brokerCount} brokers, {topicCount} topics"
		color="violet"
	/>

	<div class="space-y-2 mb-4">
		<div class="flex items-center justify-between text-xs bg-surface-800/40 rounded px-3 py-2">
			<span class="text-surface-400">Cluster ID</span>
			<span class="text-violet-400 font-mono">{clusterId || 'N/A'}</span>
		</div>
		<div class="flex items-center justify-between text-xs bg-surface-800/40 rounded px-3 py-2">
			<span class="text-surface-400">Controller</span>
			<span class="text-violet-400 font-mono">Broker {controllerId ?? 'N/A'}</span>
		</div>
	</div>

	{#if brokers.length > 0}
		<div>
			<h4 class="text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-2">
				Brokers
			</h4>
			<DataTable headers={['ID', 'Host', 'Port']}>
				{#each brokers as broker}
					<tr class="border-b border-surface-700/20 last:border-b-0 hover:bg-surface-800/40 transition-colors">
						<td class="px-3 py-2 text-violet-400">{broker.id}</td>
						<td class="px-3 py-2 text-surface-300">{broker.host}</td>
						<td class="px-3 py-2 text-right text-surface-300">{broker.port}</td>
					</tr>
				{/each}
			</DataTable>
		</div>
	{/if}
</Card>
