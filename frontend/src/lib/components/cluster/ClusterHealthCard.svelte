<script lang="ts">
	import { Card, StatusPill } from '$lib/components/ui';

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
			<!-- Brokers -->
			<div class="text-center p-4 bg-surface-hover rounded-lg">
				<div class="text-2xl font-bold text-text tabular-nums">{brokerCount}</div>
				<div class="text-xs text-text-tertiary mt-1">Brokers</div>
				{#if controllerId !== null}
					<div class="text-[10px] text-text-tertiary mt-0.5">Controller: B{controllerId}</div>
				{/if}
			</div>

			<!-- Topics -->
			<div class="text-center p-4 bg-surface-hover rounded-lg">
				<div class="text-2xl font-bold text-text tabular-nums">{topicCount}</div>
				<div class="text-xs text-text-tertiary mt-1">Topics</div>
			</div>

			<!-- Partitions -->
			<div class="text-center p-4 bg-surface-hover rounded-lg">
				<div class="text-2xl font-bold text-text tabular-nums">{totalPartitions}</div>
				<div class="text-xs text-text-tertiary mt-1">Partitions</div>
				{#if underReplicatedCount > 0}
					<div class="text-[10px] text-warning mt-0.5">{underReplicatedCount} under-replicated</div>
				{/if}
			</div>

			<!-- Consumer Groups -->
			<div class="text-center p-4 bg-surface-hover rounded-lg">
				<div class="text-2xl font-bold text-text tabular-nums">{consumerGroupCount}</div>
				<div class="text-xs text-text-tertiary mt-1">Consumer Groups</div>
			</div>
		</div>
	{/snippet}
</Card>
