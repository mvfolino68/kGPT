<script lang="ts">
	import { Card, StatusPill, StatCard } from '$lib/components/ui';

	interface Props {
		connected: boolean;
		clusterId: string | null;
		clusterName?: string | null;
		controllerId: number | null;
		brokerCount: number;
		topicCount: number;
		totalPartitions: number;
		underReplicatedCount: number;
		consumerGroupCount: number;
	}

	let {
		connected,
		clusterId,
		clusterName,
		controllerId,
		brokerCount,
		topicCount,
		totalPartitions,
		underReplicatedCount,
		consumerGroupCount
	}: Props = $props();

	const healthStatus = $derived(() => {
		if (!connected) return 'disconnected';
		if (underReplicatedCount > 0) return 'warning';
		return 'healthy';
	});
</script>

<Card title="Cluster Health" subtitle={clusterName || clusterId || ''}>
	{#snippet actions()}
		<div class="flex items-center gap-2">
			<StatusPill
				status={healthStatus() === 'healthy' ? 'success' : healthStatus() === 'warning' ? 'warning' : 'inactive'}
				size="sm"
				pulse={connected}
				label={healthStatus() === 'healthy' ? 'Healthy' : healthStatus() === 'warning' ? 'Degraded' : 'Disconnected'}
			/>
		</div>
	{/snippet}
	{#snippet children()}
		<div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
			<StatCard label="Brokers" value={brokerCount.toString()}>
				{#if controllerId !== null}
					<div class="text-[10px] text-text-tertiary mt-0.5">Controller: B{controllerId}</div>
				{/if}
			</StatCard>

			<StatCard label="Topics" value={topicCount.toString()} />

			<StatCard label="Partitions" value={totalPartitions.toString()}>
				{#if underReplicatedCount > 0}
					<div class="text-[10px] text-warning mt-0.5 font-medium">{underReplicatedCount} under-replicated</div>
				{/if}
			</StatCard>

			<StatCard label="Consumer Groups" value={consumerGroupCount.toString()} />
		</div>
	{/snippet}
</Card>
