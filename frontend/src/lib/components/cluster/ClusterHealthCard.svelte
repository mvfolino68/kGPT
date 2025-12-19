<script lang="ts">
	interface Props {
		connected: boolean;
		clusterId: string | null;
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

<div class="panel overflow-hidden">
	<!-- Header with status -->
	<div class="panel-header flex items-center justify-between">
		<div class="flex items-center gap-3">
			<div
				class="w-3 h-3 rounded-full {healthStatus() === 'healthy'
					? 'bg-emerald-400'
					: healthStatus() === 'warning'
						? 'bg-amber-400'
						: 'bg-surface-500'} {connected ? 'animate-pulse' : ''}"
			></div>
			<div>
				<h2 class="text-sm font-semibold text-surface-100">Cluster Health</h2>
				{#if clusterId}
					<p class="text-xs text-surface-500 font-mono truncate max-w-xs" title={clusterId}>
						{clusterId}
					</p>
				{/if}
			</div>
		</div>
		{#if connected}
			<span
				class="px-2.5 py-1 text-xs font-medium rounded-full {healthStatus() === 'healthy'
					? 'bg-emerald-500/10 text-emerald-400'
					: 'bg-amber-500/10 text-amber-400'}"
			>
				{healthStatus() === 'healthy' ? 'Healthy' : 'Degraded'}
			</span>
		{:else}
			<span class="px-2.5 py-1 text-xs font-medium rounded-full bg-surface-700 text-surface-400">
				Disconnected
			</span>
		{/if}
	</div>

	<!-- Metrics grid -->
	<div class="p-4">
		<div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
			<!-- Brokers -->
			<div class="text-center p-3 bg-surface-700/30 rounded-lg">
				<div class="text-2xl font-bold text-surface-100 tabular-nums">{brokerCount}</div>
				<div class="text-xs text-surface-500 mt-1">Brokers</div>
				{#if controllerId !== null}
					<div class="text-[10px] text-surface-600 mt-0.5">Controller: B{controllerId}</div>
				{/if}
			</div>

			<!-- Topics -->
			<div class="text-center p-3 bg-surface-700/30 rounded-lg">
				<div class="text-2xl font-bold text-surface-100 tabular-nums">{topicCount}</div>
				<div class="text-xs text-surface-500 mt-1">Topics</div>
			</div>

			<!-- Partitions -->
			<div class="text-center p-3 bg-surface-700/30 rounded-lg">
				<div class="text-2xl font-bold text-surface-100 tabular-nums">{totalPartitions}</div>
				<div class="text-xs text-surface-500 mt-1">Partitions</div>
				{#if underReplicatedCount > 0}
					<div class="text-[10px] text-amber-400 mt-0.5">{underReplicatedCount} under-replicated</div>
				{/if}
			</div>

			<!-- Consumer Groups -->
			<div class="text-center p-3 bg-surface-700/30 rounded-lg">
				<div class="text-2xl font-bold text-surface-100 tabular-nums">{consumerGroupCount}</div>
				<div class="text-xs text-surface-500 mt-1">Consumer Groups</div>
			</div>
		</div>
	</div>
</div>
