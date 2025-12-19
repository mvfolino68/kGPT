<script lang="ts">
	import { Button, Panel } from '$lib/components/ui';
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
			<span class="text-surface-500 animate-pulse">Loading pipeline info...</span>
		</div>
	{:else if pipelineInfo}
		<!-- RAG Overview -->
		<Panel title="RAG Pipeline Configuration">
			{#snippet children()}

			<div class="p-4">
				<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
					<div class="inner-card p-4">
						<h3 class="text-[10px] font-bold uppercase tracking-wider text-emerald-400/80 mb-3">Current Configuration</h3>
						<div class="space-y-2 text-xs">
							<div class="flex justify-between">
								<span class="text-surface-500">Embedding Model:</span>
								<span class="text-surface-300">{pipelineInfo.embedding_config.model}</span>
							</div>
							<div class="flex justify-between">
								<span class="text-surface-500">Dimensions:</span>
								<span class="text-surface-300">{pipelineInfo.embedding_config.dimensions}</span>
							</div>
							<div class="flex justify-between">
								<span class="text-surface-500">Hybrid Search:</span>
								<span class={pipelineInfo.hybrid_search_enabled ? 'text-emerald-400/80' : 'text-surface-500'}>
									{pipelineInfo.hybrid_search_enabled ? 'enabled' : 'disabled'}
								</span>
							</div>
							<div class="flex justify-between">
								<span class="text-surface-500">Reranking:</span>
								<span class={pipelineInfo.reranking_available ? 'text-emerald-400/80' : 'text-surface-400'}>
									{pipelineInfo.reranking_available ? 'available' : 'not configured'}
								</span>
							</div>
						</div>
					</div>

					<div class="inner-card p-4">
						<h3 class="text-[10px] font-bold uppercase tracking-wider text-surface-400 mb-3">Retrieval Settings</h3>
						<div class="space-y-2 text-xs">
							<div class="flex justify-between">
								<span class="text-surface-500">Initial Candidates:</span>
								<span class="text-surface-300">{pipelineInfo.retrieval_config.top_k_initial}</span>
							</div>
							<div class="flex justify-between">
								<span class="text-surface-500">Final Results:</span>
								<span class="text-surface-300">{pipelineInfo.retrieval_config.top_k_final}</span>
							</div>
							<div class="flex justify-between">
								<span class="text-surface-500">Hybrid Alpha:</span>
								<span class="text-surface-300">{pipelineInfo.retrieval_config.hybrid_alpha}</span>
							</div>
							<div class="flex justify-between">
								<span class="text-surface-500">Query Expansions:</span>
								<span class="text-surface-300">{pipelineInfo.retrieval_config.query_expansion_count}</span>
							</div>
						</div>
					</div>
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
					<input
						type="text"
						value={demoQuery}
						oninput={(e) => onDemoQueryChange(e.currentTarget.value)}
						placeholder="Enter a query to see the RAG pipeline in action..."
						class="flex-1 min-w-0 bg-surface-700/50 border-none rounded-md px-3 py-2 text-sm text-foreground placeholder:text-muted transition-all focus:outline-none focus:bg-surface-700 focus:ring-2 focus:ring-primary-600/50"
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
						<div class="inner-card p-3">
							<div class="text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-1">Total Vectors</div>
							<div class="text-xl text-surface-200">{chunkAnalytics.total_vectors.toLocaleString()}</div>
						</div>
						<div class="inner-card p-3">
							<div class="text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-1">Avg Chunk Size</div>
							<div class="text-xl text-surface-200">
								{chunkAnalytics.chunk_size_stats.avg_chars.toLocaleString()}
								<span class="text-xs text-surface-500">chars</span>
							</div>
						</div>
						<div class="inner-card p-3">
							<div class="text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-1">Est. Tokens/Chunk</div>
							<div class="text-xl text-surface-200">~{chunkAnalytics.chunk_size_stats.avg_tokens_estimate}</div>
						</div>
						<div class="inner-card p-3">
							<div class="text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-1">Index Health</div>
							<div class="text-xl {chunkAnalytics.index_health.optimizer_status === 'ok' ? 'text-emerald-400/80' : 'text-amber-400/80'}">
								{chunkAnalytics.index_health.optimizer_status}
							</div>
						</div>
					</div>

					<!-- Size Distribution -->
					<div class="mb-6">
						<h4 class="text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-3">Chunk Size Distribution</h4>
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
						<h4 class="text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-3">Source Breakdown (sampled)</h4>
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
				<span class="text-surface-500 animate-pulse">Loading analytics...</span>
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
						<textarea
								id="pipeline-embed-text-1"
							value={embedText1}
							oninput={(e) => onEmbedText1Change(e.currentTarget.value)}
							placeholder="Enter first text..."
							rows="3"
							class="w-full bg-surface-700/50 border-none rounded-md px-3 py-2 text-sm text-foreground placeholder:text-muted transition-all focus:outline-none focus:bg-surface-700 focus:ring-2 focus:ring-primary-600/50"
						></textarea>
					</div>
					<div>
							<label for="pipeline-embed-text-2" class="block text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-1">Text 2</label>
						<textarea
								id="pipeline-embed-text-2"
							value={embedText2}
							oninput={(e) => onEmbedText2Change(e.currentTarget.value)}
							placeholder="Enter second text..."
							rows="3"
							class="w-full bg-surface-700/50 border-none rounded-md px-3 py-2 text-sm text-foreground placeholder:text-muted transition-all focus:outline-none focus:bg-surface-700 focus:ring-2 focus:ring-primary-600/50"
						></textarea>
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
