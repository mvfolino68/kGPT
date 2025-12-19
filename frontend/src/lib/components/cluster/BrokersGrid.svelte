<script lang="ts">
	import type { BrokerInfo } from '$lib/api';

	interface Props {
		brokers: BrokerInfo[];
		onBrokerClick?: (brokerId: number) => void;
	}

	let { brokers, onBrokerClick }: Props = $props();

	// Calculate total partitions for percentage
	const totalPartitions = $derived(brokers.reduce((sum, b) => sum + b.partition_count, 0));

	function getPartitionPercent(count: number): number {
		if (totalPartitions === 0) return 0;
		return Math.round((count / totalPartitions) * 100);
	}
</script>

<div class="panel overflow-hidden">
	<div class="panel-header flex items-center justify-between">
		<h3 class="text-sm font-medium text-surface-200">Brokers</h3>
		<span class="text-xs text-surface-500">{brokers.length} nodes</span>
	</div>

	{#if brokers.length === 0}
		<div class="p-6 text-center text-surface-500 text-sm">No brokers available</div>
	{:else}
		<div class="p-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
			{#each brokers as broker}
				<button
					type="button"
					class="text-left p-4 rounded-lg bg-surface-700/30 hover:bg-surface-700/50 transition-colors"
					onclick={() => onBrokerClick?.(broker.id)}
				>
					<div class="flex items-center justify-between mb-3">
						<div class="flex items-center gap-2">
							<div
								class="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-sm font-bold text-primary"
							>
								{broker.id}
							</div>
							<div>
								<div class="text-sm font-medium text-surface-100">Broker {broker.id}</div>
								{#if broker.is_controller}
									<span class="text-[10px] text-primary">Controller</span>
								{/if}
							</div>
						</div>
						<div class="w-2 h-2 rounded-full bg-emerald-400"></div>
					</div>

					<div class="text-xs text-surface-500 font-mono mb-3 truncate" title="{broker.host}:{broker.port}">
						{broker.host}:{broker.port}
					</div>

					<div class="space-y-2">
						<div class="flex items-center justify-between text-xs">
							<span class="text-surface-500">Partitions</span>
							<span class="text-surface-300 font-medium tabular-nums">
								{broker.partition_count}
								<span class="text-surface-600">({getPartitionPercent(broker.partition_count)}%)</span>
							</span>
						</div>
						<div class="h-1.5 bg-surface-600 rounded-full overflow-hidden">
							<div
								class="h-full bg-primary/60 rounded-full transition-all"
								style="width: {getPartitionPercent(broker.partition_count)}%"
							></div>
						</div>
						<div class="flex items-center justify-between text-xs">
							<span class="text-surface-500">Leader for</span>
							<span class="text-surface-300 font-medium tabular-nums">{broker.leader_count} partitions</span>
						</div>
					</div>
				</button>
			{/each}
		</div>
	{/if}
</div>
