<script lang="ts">
	import { Button, Panel } from '$lib/components/ui';
	import { LoadingState } from '$lib/components/common';
	import type { VectorBrowseResponse } from './types';

	interface Props {
		browseResults: VectorBrowseResponse | null;
		browseLoading: boolean;
		showVectors: boolean;
		browseHistory: string[];
		onLoadVectors: (offset?: string) => void;
		onToggleVectors: (show: boolean) => void;
		onGoBack: () => void;
	}

	let {
		browseResults,
		browseLoading,
		showVectors,
		browseHistory,
		onLoadVectors,
		onToggleVectors,
		onGoBack
	}: Props = $props();
</script>

<div class="space-y-4">
	<!-- Browse controls -->
	<Panel title="Vector Browser">
		{#snippet children()}
			<div class="flex items-center gap-3">
				<label class="flex items-center gap-2 text-xs text-surface-400 cursor-pointer">
					<input
						type="checkbox"
						checked={showVectors}
						onchange={(e) => onToggleVectors(e.currentTarget.checked)}
						class="rounded bg-surface-700 border-surface-600"
					/>
					Show vectors
				</label>
				<Button variant="link" size="xs" onclick={() => onLoadVectors()}>
					Refresh
				</Button>
			</div>

			<div class="p-3 bg-surface-900/50 text-xs text-surface-400 mt-4">
				<span class="text-surface-300">Browse:</span> Explore the raw vectors stored in Qdrant. Each point represents a document chunk with its embedding.
			</div>
		{/snippet}
	</Panel>

	<!-- Vector list -->
	{#if browseLoading}
		<Panel padding="lg">
			<div class="text-center">
				<LoadingState message="Loading vectors..." showSpinner={false} size="sm" class="text-muted animate-pulse" />
			</div>
		</Panel>
	{:else if browseResults}
		<Panel>
			{#snippet children()}
				<div class="flex items-center justify-between mb-4">
					<span class="text-sm text-surface-300">
						{browseResults.total_count} vectors in {browseResults.collection}
					</span>
					<div class="flex gap-2">
						{#if browseHistory.length > 0}
							<Button variant="ghost" size="sm" onclick={onGoBack}>Back</Button>
						{/if}
						{#if browseResults.next_offset}
							<Button
								variant="ghost"
								size="sm"
								onclick={() => onLoadVectors(browseResults?.next_offset ?? undefined)}
							>
								Next
							</Button>
						{/if}
					</div>
				</div>

				<div class="space-y-1">
				{#each browseResults.points as point}
					<div class="p-4 hover:bg-surface-800/30 transition-colors rounded">
						<div class="flex items-start justify-between mb-2">
							<span class="text-xs text-surface-500">id: {point.id}</span>
							{#if point.vector_dimensions}
								<span class="text-xs text-surface-400">{point.vector_dimensions}d</span>
							{/if}
						</div>

						{#if point.payload?.page_content}
							<p class="text-sm text-surface-300 mb-2">
								{String(point.payload.page_content).slice(0, 300)}...
							</p>
						{/if}

						<div class="flex flex-wrap gap-2 text-xs">
							{#if point.payload?.source_name}
								<span class="px-2 py-0.5 bg-surface-800/50 text-surface-400 rounded">
									{point.payload.source_name}
								</span>
							{/if}
							{#if point.payload?.source}
								<a
									href={String(point.payload.source)}
									target="_blank"
									class="text-surface-300 hover:underline truncate max-w-xs"
								>
									{String(point.payload.source).slice(0, 50)}...
								</a>
							{/if}
						</div>

						{#if showVectors && point.vector_preview}
							<div class="mt-2 p-2 bg-surface-900/50 rounded text-xs text-surface-500">
								<span class="text-surface-400">vector:</span>
								[{point.vector_preview.map((v) => v.toFixed(4)).join(', ')}...]
							</div>
						{/if}
					</div>
				{/each}
			</div>
		{/snippet}
	</Panel>
	{/if}
</div>

