<script lang="ts">
	import type { KafkaCluster } from '$lib/api';

	interface Props {
		clusters: KafkaCluster[];
		connecting: boolean;
		onConnect: (cluster: KafkaCluster) => void;
	}

	let { clusters, connecting, onConnect }: Props = $props();
</script>

<div class="border-t border-surface-700/50 pt-4 mt-4">
	<div class="text-[10px] font-bold text-surface-500 uppercase tracking-wider mb-3">
		Saved <span class="text-surface-600">[{clusters.length}]</span>
	</div>
	<div class="space-y-2">
		{#each clusters as cluster}
			<div class="flex items-center justify-between bg-surface-800/50 border border-surface-700/50 rounded-lg px-4 py-3 hover:bg-surface-800 transition-colors">
				<div class="text-sm flex-1">
					<div class="text-surface-200">{cluster.name}</div>
					<div class="text-surface-500 text-xs">{cluster.bootstrap_servers}</div>
				</div>
				<button
					type="button"
					class="btn btn-primary btn-sm"
					onclick={() => onConnect(cluster)}
					disabled={connecting}
				>
					Connect
				</button>
			</div>
		{/each}
	</div>
</div>
