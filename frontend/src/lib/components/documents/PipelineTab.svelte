<script lang="ts">
	import { Button, Panel, LoadingState, Input, Textarea, ConfigRow, StatCard, SectionHeader, InfoCard } from '$lib/components/ui';
	import { getSimilarityColor, type RAGPipelineInfo, type RAGDemoResponse, type ChunkAnalytics } from './types';

	interface Props {
		pipelineInfo: RAGPipelineInfo | null;
		pipelineLoading: boolean;
		demoQuery: string;
		demoResult: RAGDemoResponse | null;
		demoLoading: boolean;
		chunkAnalytics: ChunkAnalytics | null;
		analyticsLoading: boolean;
		embedText1: string;
		embedText2: string;
		embedCompareResult: { cosine_similarity: number; similarity_percent: number; interpretation: string } | null;
		embedLoading: boolean;
		onDemoQueryChange: (query: string) => void;
		onRunDemo: () => void;
		onLoadAnalytics: () => void;
		onEmbedText1Change: (text: string) => void;
		onEmbedText2Change: (text: string) => void;
		onEmbedCompare: () => void;
	}

	let {
		pipelineInfo,
		pipelineLoading,
		demoQuery,
		demoResult,
		demoLoading,
		chunkAnalytics,
		analyticsLoading,
		embedText1,
		embedText2,
		embedCompareResult,
		embedLoading,
		onDemoQueryChange,
		onRunDemo,
		onLoadAnalytics,
		onEmbedText1Change,
		onEmbedText2Change,
		onEmbedCompare
	}: Props = $props();
</script>

<div class="space-y-4">
	{#if pipelineLoading}
		<div class="panel p-8 text-center">
			<LoadingState message="Loading pipeline info..." showSpinner={false} size="sm" class="text-surface-500 animate-pulse" />
		</div>
	{:else if pipelineInfo}
		<!-- RAG Overview -->
		<Panel title="RAG Pipeline Configuration">
			{#snippet children()}

			<div class="p-4">
				<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
					<InfoCard title="Current Configuration" variant="highlight">
						<div class="space-y-2 text-xs">
							<ConfigRow label="Embedding Model" value={pipelineInfo.embedding_config.model} />
							<ConfigRow label="Dimensions" value={pipelineInfo.embedding_config.dimensions} />
							<ConfigRow
								label="Hybrid Search"
								value={pipelineInfo.hybrid_search_enabled ? 'enabled' : 'disabled'}
								variant={pipelineInfo.hybrid_search_enabled ? 'success' : 'muted'}
							/>
							<ConfigRow
								label="Reranking"
								value={pipelineInfo.reranking_available ? 'available' : 'not configured'}
								variant={pipelineInfo.reranking_available ? 'success' : 'muted'}
							/>
						</div>
					</InfoCard>

					<InfoCard title="Retrieval Settings">
						<div class="space-y-2 text-xs">
							<ConfigRow label="Initial Candidates" value={pipelineInfo.retrieval_config.top_k_initial} />
							<ConfigRow label="Final Results" value={pipelineInfo.retrieval_config.top_k_final} />
							<ConfigRow label="Hybrid Alpha" value={pipelineInfo.retrieval_config.hybrid_alpha} />
							<ConfigRow label="Query Expansions" value={pipelineInfo.retrieval_config.query_expansion_count} />
						</div>
					</InfoCard>
				</div>
			</div>
		{/snippet}
	</Panel>

		<!-- Pipeline Stages -->
		<Panel title="Pipeline Stages">
			{#snippet children()}
				<div class="space-y-3">
					{#each pipelineInfo.pipeline_stages as stage, i}
						<div class="flex gap-4 items-start">
							<div class="w-8 h-8 rounded-full bg-surface-700/50 flex items-center justify-center text-sm text-surface-400 flex-shrink-0">
								{i + 1}
							</div>
							<div class="flex-1 inner-card p-3">
								<h4 class="text-sm text-surface-200 mb-1">{stage.name}</h4>
								<p class="text-xs text-surface-400 mb-2">{stage.description}</p>
								{#if stage.example}
									<p class="text-xs text-surface-500 bg-surface-900/50 rounded p-2">
										{stage.example}
									</p>
								{/if}
							</div>
						</div>
					{/each}
				</div>
		{/snippet}
	</Panel>

		<!-- Interactive Demo -->
		<Panel title="Interactive RAG Demo">
			{#snippet children()}
				<form onsubmit={(e) => { e.preventDefault(); onRunDemo(); }} class="flex gap-3 items-center">
					<Input
						type="text"
						value={demoQuery}
						oninput={(e) => onDemoQueryChange((e.target as HTMLInputElement).value)}
						placeholder="Enter a query to see the RAG pipeline in action..."
						class="flex-1 min-w-0"
					/>
					<Button
						type="submit"
						variant="primary"
						disabled={demoLoading || !demoQuery.trim()}
						loading={demoLoading}
					>
						Run Demo
					</Button>
				</form>

				{#if demoResult}
					<div class="space-y-4">
						{#each demoResult.pipeline_steps as step}
							<div class="inner-card p-4">
								<div class="flex items-center gap-2 mb-2">
									<span class="w-6 h-6 rounded-full bg-surface-700 flex items-center justify-center text-xs text-surface-300">
										{step.step}
									</span>
									<span class="text-sm text-surface-200">{step.name}</span>
								</div>
								{#if step.description}
									<p class="text-xs text-surface-400 mb-2">{step.description}</p>
								{/if}
								{#if step.output}
									<div class="bg-surface-900/50 rounded p-2 text-xs">
										<pre class="text-surface-300 overflow-x-auto">{JSON.stringify(step.output, null, 2)}</pre>
									</div>
								{/if}
								{#if step.error}
									<p class="text-xs text-red-400/80">Error: {step.error}</p>
								{/if}
							</div>
						{/each}
					</div>
				{/if}
		{/snippet}
	</Panel>

		<!-- Chunk Analytics -->
		{#if chunkAnalytics}
			<Panel title="Chunk Analytics" padding="none" class="overflow-hidden">
				{#snippet actions()}
					<Button
						variant="ghost"
						size="sm"
						onclick={onLoadAnalytics}
						disabled={analyticsLoading}
						loading={analyticsLoading}
					>
						Refresh
					</Button>
				{/snippet}
				{#snippet children()}
					<div class="p-4">
					<div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
						<StatCard label="Total Vectors" value={chunkAnalytics.total_vectors.toLocaleString()} />
						<StatCard label="Avg Chunk Size" value={chunkAnalytics.chunk_size_stats.avg_chars.toLocaleString()} unit="chars" />
						<StatCard label="Est. Tokens/Chunk" value={`~${chunkAnalytics.chunk_size_stats.avg_tokens_estimate}`} />
						<StatCard
							label="Index Health"
							value={chunkAnalytics.index_health.optimizer_status}
							variant={chunkAnalytics.index_health.optimizer_status === 'ok' ? 'success' : 'warning'}
						/>
					</div>

					<!-- Size Distribution -->
					<div class="mb-6">
						<SectionHeader>Chunk Size Distribution</SectionHeader>
						<div class="flex gap-2 h-24">
							{#each Object.entries(chunkAnalytics.size_distribution) as [range, count]}
								{@const maxCount = Math.max(...Object.values(chunkAnalytics.size_distribution))}
								{@const height = maxCount > 0 ? (count / maxCount) * 100 : 0}
								<div class="flex-1 flex flex-col items-center justify-end">
									<div
										class="w-full bg-surface-600 rounded-t transition-all"
										style="height: {height}%"
										title="{count} chunks"
									></div>
									<div class="text-xs text-surface-500 mt-1">{range}</div>
									<div class="text-xs text-surface-400">{count}</div>
								</div>
							{/each}
						</div>
					</div>

					<!-- Source Breakdown -->
					<div>
						<SectionHeader>Source Breakdown (sampled)</SectionHeader>
						<div class="space-y-2">
							{#each Object.entries(chunkAnalytics.sources).slice(0, 5) as [source, count]}
								{@const percentage = (count / chunkAnalytics.total_sampled) * 100}
								<div class="flex items-center gap-3">
									<div class="w-32 truncate text-xs text-surface-300" title={source}>{source}</div>
									<div class="flex-1 h-2 bg-surface-800 rounded-full overflow-hidden">
										<div class="h-full bg-surface-500 transition-all" style="width: {percentage}%"></div>
									</div>
									<div class="text-xs text-surface-400 w-16 text-right">{count} ({percentage.toFixed(0)}%)</div>
								</div>
							{/each}
						</div>
					</div>
					</div>
				{/snippet}
			</Panel>
		{:else if analyticsLoading}
			<div class="panel p-8 text-center">
				<LoadingState message="Loading analytics..." showSpinner={false} size="sm" class="text-surface-500 animate-pulse" />
			</div>
		{/if}

		<!-- Embedding Comparison Tool -->
		<Panel padding="none" class="overflow-hidden">
			{#snippet children()}
				<div class="px-4 py-3 flex items-center gap-2">
					<svg class="w-4 h-4 text-surface-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
					</svg>
					<span class="text-sm text-surface-300">Embedding Similarity Comparison</span>
				</div>

				<div class="p-4 space-y-4">
				<p class="text-xs text-surface-400">
					See how similar two texts are by comparing their embedding vectors.
				</p>

				<div class="grid grid-cols-2 gap-4">
					<div>
							<label for="pipeline-embed-text-1" class="block text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-1">Text 1</label>
						<Textarea
								id="pipeline-embed-text-1"
							value={embedText1}
							oninput={(e) => onEmbedText1Change((e.target as HTMLTextAreaElement).value)}
							placeholder="Enter first text..."
							rows={3}
						/>
					</div>
					<div>
							<label for="pipeline-embed-text-2" class="block text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-1">Text 2</label>
						<Textarea
								id="pipeline-embed-text-2"
							value={embedText2}
							oninput={(e) => onEmbedText2Change((e.target as HTMLTextAreaElement).value)}
							placeholder="Enter second text..."
							rows={3}
						/>
					</div>
				</div>

				<Button
					variant="primary"
					onclick={onEmbedCompare}
					disabled={embedLoading || !embedText1.trim() || !embedText2.trim()}
					loading={embedLoading}
				>
					Compare Embeddings
				</Button>

				{#if embedCompareResult}
					<div class="inner-card p-4 flex items-center gap-6">
						<div class="text-center">
							<div class="text-3xl {getSimilarityColor(embedCompareResult.similarity_percent)}">
								{embedCompareResult.similarity_percent}%
							</div>
							<div class="text-xs text-surface-500">similarity</div>
						</div>
						<div class="flex-1">
							<div class="h-4 bg-surface-800 rounded-full overflow-hidden">
								<div
									class="h-full bg-surface-500 transition-all duration-500"
									style="width: {embedCompareResult.similarity_percent}%"
								></div>
							</div>
						</div>
						<div class="text-right">
							<div class="text-sm text-surface-300">{embedCompareResult.interpretation}</div>
							<div class="text-xs text-surface-500">cosine: {embedCompareResult.cosine_similarity.toFixed(4)}</div>
						</div>
					</div>
				{/if}
			</div>
			{/snippet}
		</Panel>
	{/if}
</div>
