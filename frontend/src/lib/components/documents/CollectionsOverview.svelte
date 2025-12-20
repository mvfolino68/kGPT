<script lang="ts">
	import { Panel, StatusDot, StatusPill, StatCard, InnerCard, SectionHeader, ConfigRow } from '$lib/components/ui';
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
				<InnerCard padding="md">
					<!-- Header -->
					<div class="flex items-center justify-between mb-4">
						<div class="flex items-center gap-3">
							<span class="text-lg font-medium text-surface-500">{col.name}</span>
							<StatusPill status={collectionStatus(col.status).pillStatus} label={collectionStatus(col.status).label} size="sm" />
							{#if col.optimizer_status === 'ok'}
								<StatusPill status="success" label="Optimizer" sublabel="OK" size="sm" />
							{/if}
						</div>
						<span class="text-2xl font-light text-surface-200">
							{col.vectors_count.toLocaleString()}
							<span class="text-sm text-surface-500 font-normal">vectors</span>
						</span>
					</div>

					<!-- Stats Grid -->
					<div class="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
						<StatCard label="Dimensions" value={col.dimensions.toString()} size="sm" />
						<StatCard label="Distance" value={col.distance_metric} size="sm" />
						<StatCard label="Est. Size" value="~{estimateStorageSize(col.vectors_count, col.dimensions)}" size="sm" />
						<StatCard label="Segments" value={(col.segments_count || 0).toString()} size="sm" />
					</div>

					<!-- HNSW Config -->
					{#if col.hnsw_config}
						<div class="pt-2 border-t border-white/5">
							<SectionHeader spacing="md">HNSW Index Configuration</SectionHeader>
							<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-x-8 gap-y-1">
								<ConfigRow label="m" value={col.hnsw_config.m ?? 16} variant="minimal" />
								<ConfigRow label="ef_construct" value={col.hnsw_config.ef_construct ?? 100} variant="minimal" />
								<ConfigRow label="full_scan_threshold" value={col.hnsw_config.full_scan_threshold?.toLocaleString() ?? '10k'} variant="minimal" />
								<ConfigRow label="on_disk" value={col.hnsw_config.on_disk ? 'yes' : 'no (RAM)'} variant="minimal" />
							</div>
						</div>
					{/if}

					<!-- Storage Mode -->
					<div class="flex gap-4 mt-4 text-xs flex-wrap pt-2 border-t border-white/5">
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
								<span class="w-1.5 h-1.5 rounded-full bg-surface-400"></span>
								<span class="text-surface-400">quantization: {col.quantization_config.type}</span>
							</div>
						{:else}
							<div class="flex items-center gap-2">
								<span class="w-1.5 h-1.5 rounded-full bg-surface-600"></span>
								<span class="text-surface-500">no quantization</span>
							</div>
						{/if}
					</div>
				</InnerCard>
			{/each}
			</div>
		{/snippet}
	</Panel>
{:else}
	<Panel title="Collections" subtitle="Qdrant collections">
		<div class="p-8 text-center">
			<Icon name="search" size="lg" class="text-surface-600 mb-2" />
			<p class="text-surface-500">No collections found</p>
		</div>
	</Panel>
{/if}
