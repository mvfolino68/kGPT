<script lang="ts">
	import { estimateStorageSize, type CollectionsResponse } from './types';

	interface Props {
		collections: CollectionsResponse;
	}

	let { collections }: Props = $props();
</script>

{#if collections.collections.length > 0}
	<div class="panel overflow-hidden">
		<div class="panel-header flex items-center gap-2">
			<span class="text-surface-400 text-xs">DB</span>
			<span class="text-sm text-surface-300">Qdrant Collections</span>
		</div>
		<div class="p-4 space-y-4">
			{#each collections.collections as col}
				<div class="inner-card p-4">
					<!-- Header -->
					<div class="flex items-center justify-between mb-4">
						<div class="flex items-center gap-3">
							<span class="text-lg text-surface-100">{col.name}</span>
							<span class="px-2 py-0.5 text-xs rounded {col.status === 'green' ? 'bg-emerald-500/10 text-emerald-400/80' : 'bg-amber-500/10 text-amber-400/80'}">
								{col.status}
							</span>
							{#if col.optimizer_status === 'ok'}
								<span class="px-2 py-0.5 text-xs rounded bg-surface-700/50 text-surface-300">
									optimizer: ok
								</span>
							{/if}
						</div>
						<span class="text-2xl text-surface-200">
							{col.vectors_count.toLocaleString()}
							<span class="text-sm text-surface-500">vectors</span>
						</span>
					</div>

					<!-- Stats Grid -->
					<div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
						<div class="bg-surface-900/50 rounded p-3">
							<div class="text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-1">Dimensions</div>
							<div class="text-lg text-surface-200">{col.dimensions}</div>
						</div>
						<div class="bg-surface-900/50 rounded p-3">
							<div class="text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-1">Distance</div>
							<div class="text-lg text-surface-200">{col.distance_metric}</div>
						</div>
						<div class="bg-surface-900/50 rounded p-3">
							<div class="text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-1">Est. Size</div>
							<div class="text-lg text-surface-300">~{estimateStorageSize(col.vectors_count, col.dimensions)}</div>
						</div>
						<div class="bg-surface-900/50 rounded p-3">
							<div class="text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-1">Segments</div>
							<div class="text-lg text-surface-300">{col.segments_count || 0}</div>
						</div>
					</div>

					<!-- HNSW Config -->
					{#if col.hnsw_config}
						<div class="border-t border-surface-700/20 pt-4 mt-4">
							<div class="text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-2">
								HNSW Index Configuration
							</div>
							<div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
								<div class="flex justify-between">
									<span class="text-surface-500">m:</span>
									<span class="text-surface-300">{col.hnsw_config.m ?? 16}</span>
								</div>
								<div class="flex justify-between">
									<span class="text-surface-500">ef_construct:</span>
									<span class="text-surface-300">{col.hnsw_config.ef_construct ?? 100}</span>
								</div>
								<div class="flex justify-between">
									<span class="text-surface-500">full_scan_threshold:</span>
									<span class="text-surface-300">{col.hnsw_config.full_scan_threshold?.toLocaleString() ?? '10k'}</span>
								</div>
								<div class="flex justify-between">
									<span class="text-surface-500">on_disk:</span>
									<span class="text-surface-300">
										{col.hnsw_config.on_disk ? 'yes' : 'no (RAM)'}
									</span>
								</div>
							</div>
						</div>
					{/if}

					<!-- Storage Mode -->
					<div class="flex gap-4 mt-4 text-xs flex-wrap">
						<div class="flex items-center gap-2">
							<span class="w-2 h-2 rounded-full {col.on_disk_vectors === true ? 'bg-amber-400/60' : 'bg-emerald-400/60'}"></span>
							<span class="text-surface-400">vectors: {col.on_disk_vectors === true ? 'disk' : 'RAM'}</span>
						</div>
						<div class="flex items-center gap-2">
							<span class="w-2 h-2 rounded-full {col.on_disk_payload === true ? 'bg-amber-400/60' : 'bg-emerald-400/60'}"></span>
							<span class="text-surface-400">payload: {col.on_disk_payload === true ? 'disk' : 'RAM'}</span>
						</div>
						{#if col.quantization_config}
							<div class="flex items-center gap-2">
								<span class="w-2 h-2 rounded-full bg-surface-400"></span>
								<span class="text-surface-400">quantization: {col.quantization_config.type}</span>
							</div>
						{:else}
							<div class="flex items-center gap-2">
								<span class="w-2 h-2 rounded-full bg-surface-600"></span>
								<span class="text-surface-500">no quantization</span>
							</div>
						{/if}
					</div>
				</div>
			{/each}
		</div>
	</div>
{/if}
