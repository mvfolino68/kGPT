<script lang="ts">
	import type { BrokerInfo } from '$lib/api';
	import { Card, Button } from '$lib/components/ui';

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

<Card title="Brokers" subtitle="{brokers.length} nodes">
	{#snippet children()}
		{#if brokers.length === 0}
			<div class="text-center text-text-tertiary text-sm py-2">No brokers available</div>
		{:else}
			<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
				{#each brokers as broker}
					<Button
						variant="secondary"
						size="lg"
						class="w-full justify-start text-left p-4 rounded-lg bg-surface-hover hover:bg-surface-active"
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
									<div class="text-sm font-medium text-text">Broker {broker.id}</div>
									{#if broker.is_controller}
										<span class="text-[10px] text-primary">Controller</span>
									{/if}
								</div>
							</div>
							<div class="w-2.5 h-2.5 rounded-full bg-success shadow-[0_0_8px_rgba(52,211,153,0.5)]"></div>
						</div>

						<div class="text-xs text-text-tertiary font-mono mb-3 truncate" title="{broker.host}:{broker.port}">
							{broker.host}:{broker.port}
						</div>

						<div class="space-y-2">
							<div class="flex items-center justify-between text-xs">
								<span class="text-text-tertiary">Partitions</span>
								<span class="text-text-secondary font-medium tabular-nums">
									{broker.partition_count}
									<span class="text-text-tertiary">({getPartitionPercent(broker.partition_count)}%)</span>
								</span>
							</div>
							<div class="h-1.5 bg-bg-elevated rounded-full overflow-hidden">
								<div
									class="h-full bg-primary/60 rounded-full transition-all"
									style="width: {getPartitionPercent(broker.partition_count)}%"
								></div>
							</div>
							<div class="flex items-center justify-between text-xs">
								<span class="text-text-tertiary">Leader for</span>
								<span class="text-text-secondary font-medium tabular-nums">{broker.leader_count} partitions</span>
							</div>
						</div>
					</Button>
				{/each}
			</div>
		{/if}
	{/snippet}
</Card>

