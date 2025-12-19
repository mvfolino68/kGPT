<script lang="ts">
	import { StatusIndicator } from '$lib/components';
	import { getSimilarityColor, type VectorSearchResponse, type ChunkResult } from './types';

	interface Props {
		searchQuery: string;
		searchResults: VectorSearchResponse | null;
		searchLoading: boolean;
		searchK: number;
		onQueryChange: (query: string) => void;
		onKChange: (k: number) => void;
		onSearch: () => void;
	}

	let {
		searchQuery,
		searchResults,
		searchLoading,
		searchK,
		onQueryChange,
		onKChange,
		onSearch
	}: Props = $props();

	let selectedChunk = $state<ChunkResult | null>(null);
</script>

<div class="space-y-4">
	<!-- Search interface -->
	<div class="panel overflow-hidden">
		<div class="panel-header flex items-center gap-2">
			<svg class="w-4 h-4 text-surface-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
				<path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
			</svg>
			<span class="text-sm text-surface-300">Semantic Vector Search</span>
		</div>

		<div class="p-4 space-y-4">
			<div class="p-3 bg-surface-800/30 rounded-lg text-xs text-surface-400">
				<span class="text-surface-300">How it works:</span> Your query is converted to an embedding vector, then compared against all stored document chunks using cosine similarity.
			</div>

			<form onsubmit={(e) => { e.preventDefault(); onSearch(); }} class="flex gap-3 items-center">
				<input
					type="text"
					value={searchQuery}
					oninput={(e) => onQueryChange(e.currentTarget.value)}
					placeholder="Search for anything..."
					class="flex-1 min-w-0 input"
				/>
				<select
					value={searchK}
					onchange={(e) => onKChange(parseInt(e.currentTarget.value))}
					class="input w-auto"
				>
					<option value={5}>Top 5</option>
					<option value={10}>Top 10</option>
					<option value={20}>Top 20</option>
				</select>
				<button
					type="submit"
					disabled={searchLoading || !searchQuery.trim()}
					class="btn btn-primary"
				>
					{searchLoading ? 'Searching...' : 'Search'}
				</button>
			</form>
		</div>
	</div>

	<!-- Search results -->
	{#if searchResults}
		<div class="panel overflow-hidden">
			<div class="panel-header flex items-center gap-2">
				<StatusIndicator status="active" size="sm" />
				<span class="text-sm text-surface-300">
					{searchResults.total} results for "{searchResults.query}"
				</span>
			</div>

			<div class="divide-y divide-surface-700/20">
				{#each searchResults.chunks as chunk, i}
					<div class="p-4 hover:bg-surface-800/20 transition-colors">
						<div class="flex items-start justify-between mb-2">
							<div class="flex items-center gap-3">
								<span class="text-surface-500 text-xs">#{i + 1}</span>
								<span class="text-xs px-2 py-0.5 rounded bg-surface-800/50 {getSimilarityColor(chunk.similarity_percent)}">
									{chunk.similarity_percent}% match
								</span>
								<span class="text-surface-500 text-xs">from: {chunk.source_name}</span>
							</div>
							<button
								onclick={() => selectedChunk = selectedChunk === chunk ? null : chunk}
								class="text-xs text-surface-400 hover:text-surface-200 transition-colors"
							>
								{selectedChunk === chunk ? 'Hide' : 'Details'}
							</button>
						</div>

						<p class="text-sm text-surface-300 leading-relaxed">{chunk.content_preview}</p>

						{#if selectedChunk === chunk}
							<div class="mt-3 p-3 bg-surface-900/50 rounded-lg text-xs space-y-2">
								<div>
									<span class="text-surface-500">similarity_score:</span>
									<span class="text-surface-200 ml-2">{chunk.similarity_score.toFixed(4)}</span>
								</div>
								<div>
									<span class="text-surface-500">source:</span>
									<a href={chunk.source} target="_blank" class="text-surface-300 ml-2 hover:underline">
										{chunk.source}
									</a>
								</div>
								<div>
									<span class="text-surface-500">metadata:</span>
									<pre class="mt-1 text-surface-300 overflow-x-auto">{JSON.stringify(chunk.metadata, null, 2)}</pre>
								</div>
							</div>
						{/if}
					</div>
				{/each}
			</div>
		</div>
	{/if}
</div>
