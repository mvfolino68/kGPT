<script lang="ts">
	import { Panel, StatusDot, StatusPill } from '$lib/components/ui';
	import { estimateStorageSize, type CollectionsResponse } from './types';

	interface Props {
		collections: CollectionsResponse;
	}

	let { collections }: Props = $props();

	function collectionStatus(status: string): { pillStatus: 'success' | 'warning' | 'error' | 'inactive'; label: string } {
		if (status === 'green') return { pillStatus: 'success', label: 'Healthy' };
		if (status === 'yellow') return { pillStatus: 'warning', label: 'Degraded' };
		if (status === 'red') return { pillStatus: 'error', label: 'Error' };
		return { pillStatus: 'inactive', label: 'Unknown' };
	}
</script>

{#if collections.collections.length > 0}
	<Panel title="Collections" subtitle="Qdrant collections" padding="none">
		{#snippet children()}
			<div class="p-4 space-y-4">
			{#each collections.collections as col}
				<div class="inner-card p-4">
					<!-- Header -->
					<div class="flex items-center justify-between mb-4">
						<div class="flex items-center gap-3">
							<span class="text-lg text-surface-100">{col.name}</span>
							<StatusPill status={collectionStatus(col.status).pillStatus} label={collectionStatus(col.status).label} size="sm" />
							{#if col.optimizer_status === 'ok'}
								<StatusPill status="success" label="Optimizer" sublabel="OK" size="sm" />
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
						<div class="pt-4 mt-4">
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
							<StatusDot status={col.on_disk_vectors === true ? 'warning' : 'success'} size="sm" />
							<span class="text-surface-400">vectors: {col.on_disk_vectors === true ? 'disk' : 'RAM'}</span>
						</div>
						<div class="flex items-center gap-2">
							<StatusDot status={col.on_disk_payload === true ? 'warning' : 'success'} size="sm" />
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
		{/snippet}
	</Panel>
{/if}
