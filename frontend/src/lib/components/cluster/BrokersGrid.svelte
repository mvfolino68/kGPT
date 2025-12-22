<script lang="ts">
	import { type BrokerInfo } from '$lib/api';
	import { Card, Button, Icon } from '$lib/components/ui';
	import BrokerConfigModal from './BrokerConfigModal.svelte';

	interface Props {
		brokers: BrokerInfo[];
		onBrokerClick?: (brokerId: number) => void;
	}

	let { brokers, onBrokerClick }: Props = $props();

	let selectedBrokerId = $state<number | null>(null);

	// Calculate total partitions for percentage
	const totalPartitions = $derived(brokers.reduce((sum, b) => sum + b.partition_count, 0));

	function getPartitionPercent(count: number): number {
		if (totalPartitions === 0) return 0;
		return Math.round((count / totalPartitions) * 100);
	}

	function handleConfig(brokerId: number) {
		selectedBrokerId = brokerId;
	}
</script>

<Card title="Brokers" subtitle="{brokers.length} {brokers.length === 1 ? 'node' : 'nodes'}">
	{#snippet children()}
		{#if brokers.length === 0}
			<div class="text-center text-text-tertiary text-sm py-2">No brokers available</div>
		{:else}
			<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
				{#each brokers as broker}
					<div
						class="w-full justify-start text-left p-4 rounded-lg bg-surface-hover hover:bg-surface-active transition-colors"
					>
						<div class="flex items-start gap-4 w-full">
							<!-- Left: Broker identity -->
							<div class="flex items-center gap-3 shrink-0">
								<div
									class="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-base font-bold text-primary"
								>
									{broker.id}
								</div>
								<div>
									<div class="text-sm font-semibold text-text">Broker {broker.id}</div>
									<div class="flex items-center gap-2 mt-0.5">
										<span class="w-2 h-2 rounded-full bg-success shadow-[0_0_6px_rgba(52,211,153,0.5)]"></span>
										<span class="text-xs text-text-tertiary font-mono" title="{broker.host}:{broker.port}">{broker.host}:{broker.port}</span>
									</div>
									{#if broker.is_controller}
										<span class="inline-block mt-1 text-[10px] font-medium text-primary bg-primary/10 px-1.5 py-0.5 rounded">Controller</span>
									{/if}
								</div>
							</div>

							<!-- Middle: Stats -->
							<div class="flex-1 space-y-2 min-w-0 mx-2">
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
									<span class="text-text-secondary font-medium tabular-nums">{broker.leader_count} {broker.leader_count === 1 ? 'partition' : 'partitions'}</span>
								</div>
							</div>

							<!-- Right: Actions -->
							<div class="flex flex-col gap-1 shrink-0">
                                <Button
									variant="ghost"
									size="icon-sm"
									class="text-text-tertiary hover:text-primary hover:bg-primary/10 w-6 h-6"
									onclick={(e) => {
										e.stopPropagation();
										handleConfig(broker.id);
									}}
									title="Inspect Config"
								>
									<Icon name="settings" size="xs" />
								</Button>
							</div>
						</div>
					</div>
				{/each}
			</div>
		{/if}

		<BrokerConfigModal
			brokerId={selectedBrokerId}
			onClose={() => selectedBrokerId = null}
		/>
	{/snippet}
</Card>

