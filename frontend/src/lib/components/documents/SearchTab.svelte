<script lang="ts">
	import { Button, Panel, Card, Icon, Input, Select } from '$lib/components/ui';
	import { StatusPill } from '$lib/components';
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

<div class="space-y-6">
	<!-- Search interface -->
	<Card padding="none" class="overflow-hidden">
		{#snippet children()}
			<div class="px-4 py-3 flex items-center gap-2 border-b border-white/5 bg-surface-800/50">
				<Icon name="search" class="text-surface-400" size="sm" />
				<span class="text-sm font-medium text-surface-200">Semantic Vector Search</span>
			</div>

			<div class="p-4 space-y-4">
				<div class="p-3 bg-surface-900/50 rounded-lg text-xs text-surface-400 border border-surface-800 flex gap-2">
					<Icon name="info" size="xs" class="shrink-0 mt-0.5 text-surface-500" />
					<div class="leading-relaxed">
						<span class="text-surface-300 font-medium">How it works:</span> Your query is converted to an embedding vector, then compared against all stored document chunks using cosine similarity.
					</div>
				</div>

				<form onsubmit={(e) => { e.preventDefault(); onSearch(); }} class="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center">
					<div class="relative flex-1">
						<div class="absolute left-3 top-1/2 -translate-y-1/2 text-surface-500 z-10">
							<Icon name="search" size="sm" />
						</div>
						<Input
							type="text"
							value={searchQuery}
							oninput={(e) => onQueryChange((e.target as HTMLInputElement).value)}
							placeholder="Search for anything..."
							class="pl-10"
						/>
					</div>

					<div class="flex gap-2">
						<Select
							value={searchK}
							options={[
								{ value: 5, label: 'Top 5' },
								{ value: 10, label: 'Top 10' },
								{ value: 20, label: 'Top 20' }
							]}
							onchange={(e) => onKChange(parseInt((e.target as HTMLSelectElement).value))}
							class="w-[100px]"
						/>
						<Button
							type="submit"
							variant="primary"
							disabled={searchLoading || !searchQuery.trim()}
							loading={searchLoading}
							class="min-w-[100px]"
						>
							Search
						</Button>
					</div>
				</form>
			</div>
		{/snippet}
	</Card>

	<!-- Search results -->
	{#if searchResults}
		<div class="animate-in fade-in slide-in-from-bottom-2 duration-300">
			{#if searchResults.chunks.length > 0}
				<div class="flex items-center gap-2 mb-4 px-1">
					<StatusPill status="success" label="Results" size="sm" />
					<span class="text-sm text-surface-300">
						Found {searchResults.total} matches for "<span class="text-surface-100">{searchResults.query}</span>"
					</span>
				</div>

				<div class="space-y-3">
					{#each searchResults.chunks as chunk, i}
						<Card variant="subtle" class="hover:border-primary/20 transition-colors group">
							{#snippet children()}
								<div class="flex items-start justify-between gap-4 mb-2">
									<div class="flex items-center gap-3">
										<span class="text-surface-500 text-xs font-mono">#{i + 1}</span>
										<span class="text-xs px-2 py-0.5 rounded-full bg-surface-900/50 font-medium border border-surface-700/50 {getSimilarityColor(chunk.similarity_percent)}">
											{chunk.similarity_percent}% match
										</span>
										<div class="flex items-center gap-1.5 text-surface-400 text-xs">
											<Icon name="file-text" size="xs" />
											<span class="truncate max-w-[200px]">{chunk.source_name}</span>
										</div>
									</div>
									<Button
										variant="ghost"
										size="xs"
										class="opacity-0 group-hover:opacity-100 transition-opacity"
										onclick={() => selectedChunk = selectedChunk === chunk ? null : chunk}
									>
										{selectedChunk === chunk ? 'Less info' : 'More info'}
									</Button>
								</div>

								<div class="pl-7">
									<p class="text-sm text-surface-300 leading-relaxed line-clamp-3 group-hover:line-clamp-none transition-all duration-200">
										{chunk.content_preview}
									</p>

									{#if selectedChunk === chunk}
										<div class="mt-4 p-4 bg-surface-900/50 rounded-lg text-xs space-y-3 border border-surface-800/50 animate-in fade-in zoom-in-95 duration-200">
											<div class="grid grid-cols-2 gap-4">
												<div>
													<span class="text-surface-500 block mb-1 uppercase tracking-wider text-[10px]">Score</span>
													<span class="text-surface-200 font-mono">{chunk.similarity_score.toFixed(4)}</span>
												</div>
												<div>
													<span class="text-surface-500 block mb-1 uppercase tracking-wider text-[10px]">Source</span>
													{#if chunk.source.startsWith('http')}
														<a href={chunk.source} target="_blank" class="text-primary hover:underline flex items-center gap-1">
															{chunk.source}
															<Icon name="external-link" size="xs" />
														</a>
													{:else}
														<span class="text-surface-200">{chunk.source}</span>
													{/if}
												</div>
											</div>
											<div>
												<span class="text-surface-500 block mb-1 uppercase tracking-wider text-[10px]">Metadata</span>
												<pre class="bg-surface-950/50 p-2 rounded border border-surface-800 overflow-x-auto text-surface-300 font-mono">{JSON.stringify(chunk.metadata, null, 2)}</pre>
											</div>
										</div>
									{/if}
								</div>
							{/snippet}
						</Card>
					{/each}
				</div>
			{:else}
				<div class="text-center py-12 bg-surface-800/30 rounded-xl border border-dashed border-surface-700/50">
					<div class="inline-flex items-center justify-center w-12 h-12 rounded-full bg-surface-800/50 mb-4 text-surface-500">
						<Icon name="search-x" size="md" />
					</div>
					<h3 class="text-sm font-medium text-surface-200">No results found</h3>
					<p class="text-xs text-surface-400 mt-1">Try adjusting your search terms or lowering the match threshold.</p>
				</div>
			{/if}
		</div>
	{/if}
</div>
