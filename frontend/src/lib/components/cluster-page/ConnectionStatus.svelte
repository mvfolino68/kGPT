<script lang="ts">
	import { Button, Card } from '$lib/components/ui';
	import type { ClusterInfo } from '$lib/api';
	import { StatusIndicator } from '$lib/components';
	import kafkaLogo from '$lib/assets/kafka-logo.svg';
	import ClusterStats from './ClusterStats.svelte';
	import TopicsChips from './TopicsChips.svelte';
	import OperationsPanel from './OperationsPanel.svelte';

	interface Props {
		clusterInfo: Partial<ClusterInfo> & { connected: boolean };
		loading: boolean;
		onDisconnect: () => void;
	}

	let { clusterInfo, loading, onDisconnect }: Props = $props();
</script>

<Card
	padding="none"
	variant="glass"
	class="bg-surface-900 ring-0 border {clusterInfo.connected ? 'border-success/30' : 'border-surface-700/50'}"
>
	{#snippet header()}
		<div class="flex items-center justify-between">
			<div class="flex items-center gap-3">
				<StatusIndicator
					status={clusterInfo.connected ? 'active' : 'inactive'}
					size="lg"
					pulse={clusterInfo.connected}
				/>
				<span class="text-[10px] font-bold text-surface-500 uppercase tracking-wider">Connection Status</span>
			</div>
			{#if loading}
				<span class="text-xs text-surface-500">Checking...</span>
			{/if}
		</div>
	{/snippet}

	{#snippet children()}
		<div class="p-4">
			{#if loading}
				<div class="py-8 text-center text-surface-500 flex items-center justify-center gap-2">
					<StatusIndicator status="warning" pulse />
					<span>Scanning for clusters...</span>
				</div>
			{:else if clusterInfo.connected}
				<div class="space-y-4">
					<div class="flex items-center gap-3">
						<span class="text-2xl font-bold text-success">Connected</span>
					</div>

					<ClusterStats
						clusterId={clusterInfo.cluster_id}
						brokers={clusterInfo.brokers || 0}
						topics={clusterInfo.topics?.length || 0}
						groups={clusterInfo.consumer_groups?.length || 0}
					/>

					{#if clusterInfo.topics && clusterInfo.topics.length > 0}
						<TopicsChips topics={clusterInfo.topics} />
					{/if}

					<OperationsPanel />

					<div class="pt-4 border-t border-surface-700/50">
						<Button variant="danger-solid" size="sm" onclick={onDisconnect}>
							Disconnect
						</Button>
					</div>
				</div>
			{:else}
				<div class="py-8 text-center">
					<img src={kafkaLogo} alt="Kafka" class="w-16 h-16 mx-auto mb-4 opacity-40" />
					<div class="flex items-center justify-center gap-2 mb-2">
						<StatusIndicator status="inactive" />
						<span class="text-surface-400 text-sm uppercase tracking-wider">Disconnected</span>
					</div>
					<p class="text-xs text-surface-600 mt-1">Connect to a Kafka cluster below</p>
				</div>
			{/if}
		</div>
	{/snippet}
</Card>
