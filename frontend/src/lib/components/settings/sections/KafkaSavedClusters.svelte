<script lang="ts">
	import { Button, SectionHeader, Icon, DeleteConfirmButton } from '$lib/components/ui';
	import type { KafkaCluster } from '$lib/api';

	interface Props {
		clusters: KafkaCluster[];
		connecting: boolean;
		onconnect: (cluster: KafkaCluster) => void;
		ondisconnect: () => void;
		ondelete?: (clusterId: number) => void;
	}

	let { clusters, connecting, onconnect, ondisconnect, ondelete }: Props = $props();
</script>

<div class="pt-2">
	<SectionHeader spacing="sm" class="px-1">Saved Clusters</SectionHeader>
	<div class="space-y-2">
		{#each clusters as cluster}
			<div class="group flex items-center gap-2 p-3 bg-surface-800/30 hover:bg-surface-800/80 border border-transparent hover:border-surface-700/50 rounded-lg transition-all duration-200">
				<div class="w-2 h-2 rounded-full {cluster.is_active ? 'bg-emerald-500 shadow-sm shadow-emerald-500/50' : 'bg-surface-600'} shrink-0"></div>
				<div class="flex-1 min-w-0 grid gap-0.5">
					<span class="text-sm font-medium text-surface-200 truncate">{cluster.name}</span>
					<span class="text-xs text-surface-500 font-mono truncate">{cluster.bootstrap_servers}</span>
				</div>

				<div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
					{#if !cluster.is_active}
						<Button
							variant="ghost"
							size="sm"
							class="h-7 px-2 text-xs"
							onclick={() => onconnect(cluster)}
							disabled={connecting}
						>
							Connect
						</Button>
						{#if ondelete && cluster.id}
							<DeleteConfirmButton
								itemId={cluster.id}
								onConfirm={(id) => ondelete!(id)}
								title="Delete cluster"
							/>
						{/if}
					{:else}
						<Button
							variant="ghost"
							size="sm"
							class="h-7 px-2 text-xs text-red-400 hover:text-red-300 hover:bg-red-400/10"
							onclick={ondisconnect}
						>
							Disconnect
						</Button>
					{/if}
				</div>
			</div>
		{/each}
	</div>
</div>
