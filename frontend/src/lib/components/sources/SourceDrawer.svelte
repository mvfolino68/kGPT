<script lang="ts">
	import type { Source } from './types';

	interface Props {
		source: Source | null;
		onClose: () => void;
	}

	let { source, onClose }: Props = $props();

	function getTypeConfig(type: Source['type']) {
		switch (type) {
			case 'doc':
				return {
					label: 'Documentation',
					description: 'Retrieved from indexed Kafka documentation using RAG (Retrieval-Augmented Generation)',
					color: 'text-primary-light',
					bg: 'bg-primary/10',
					border: 'border-primary/30'
				};
			case 'web':
				return {
					label: 'Web Search',
					description: 'Found via real-time web search using Exa for current information',
					color: 'text-primary-light',
					bg: 'bg-primary/10',
					border: 'border-primary/30'
				};
			case 'cluster':
				return {
					label: 'Cluster Info',
					description: 'Live data from your connected Kafka cluster',
					color: 'text-amber-400',
					bg: 'bg-amber-500/10',
					border: 'border-amber-500/30'
				};
			default:
				return {
					label: 'Source',
					description: 'Reference source',
					color: 'text-surface-400',
					bg: 'bg-surface-500/10',
					border: 'border-surface-500/30'
				};
		}
	}

	function formatScore(score: number | undefined): string {
		if (score === undefined) return 'N/A';
		return `${Math.round(score * 100)}%`;
	}

	function extractDomain(url: string): string {
		if (!url) return '';
		try {
			return new URL(url).hostname.replace('www.', '');
		} catch {
			return url;
		}
	}

	function handleBackdropClick(event: MouseEvent) {
		if (event.target === event.currentTarget) {
			onClose();
		}
	}

	function handleKeydown(event: KeyboardEvent) {
		if (source && event.key === 'Escape') {
			onClose();
		}
	}

	const typeConfig = $derived(source ? getTypeConfig(source.type) : null);
</script>

<svelte:window onkeydown={handleKeydown} />

{#if source && typeConfig}
	<!-- Backdrop -->
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
		onclick={handleBackdropClick}
	>
		<!-- Drawer -->
		<!-- svelte-ignore a11y_click_events_have_key_events -->
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
		<aside
			class="absolute right-0 top-0 h-full w-full max-w-md
				bg-surface-900 border-l border-surface-700/50 shadow-2xl
				animate-slide-in overflow-hidden flex flex-col"
			onclick={(e) => e.stopPropagation()}
		>

			<!-- Header -->
			<header class="flex-shrink-0 p-4 border-b border-surface-700/50 {typeConfig.bg}">
				<div class="flex items-start justify-between gap-3">
					<div class="flex-1 min-w-0">
						<!-- Type badge -->
						<div class="flex items-center gap-2 mb-2">
							<span class="inline-flex items-center gap-1.5 px-2 py-1 rounded
								{typeConfig.bg} {typeConfig.color} {typeConfig.border} border
								text-[10px] font-bold uppercase tracking-wider">
								{typeConfig.label}
							</span>
							{#if source.relevance_score !== undefined}
								<span class="text-xs text-surface-400">
									{formatScore(source.relevance_score)} match
								</span>
							{/if}
						</div>

						<!-- Title -->
						<h2 class="text-lg font-semibold text-surface-100 leading-snug">
							{source.title}
						</h2>

						<!-- URL -->
						{#if source.url}
							<a
								href={source.url}
								target="_blank"
								rel="noopener noreferrer"
								class="inline-flex items-center gap-1.5 mt-2 text-sm {typeConfig.color} hover:underline"
							>
								<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
									<path stroke-linecap="round" stroke-linejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
								</svg>
								{extractDomain(source.url)}
							</a>
						{/if}
					</div>

					<button
						type="button"
						class="flex-shrink-0 p-2 rounded-lg hover:bg-surface-800
							transition-colors text-surface-400 hover:text-surface-200"
						onclick={onClose}
						aria-label="Close drawer"
					>
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
						</svg>
					</button>
				</div>
			</header>

			<!-- Content -->
			<div class="flex-1 overflow-y-auto">
				<!-- How this source was found -->
				<section class="p-4 border-b border-surface-700/50">
					<h3 class="text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-2">
						How This Source Was Found
					</h3>
					<p class="text-sm text-surface-300 leading-relaxed">
						{typeConfig.description}
					</p>

					{#if source.metadata?.search_query}
						<div class="mt-3 p-2 rounded-lg bg-surface-800/50 border border-surface-700/50">
							<span class="text-[10px] text-surface-500 uppercase">Search Query</span>
							<p class="text-sm text-surface-300 mt-1">"{source.metadata.search_query}"</p>
						</div>
					{/if}
				</section>

				<!-- Highlights (for web sources) -->
				{#if source.highlights && source.highlights.length > 0}
					<section class="p-4 border-b border-surface-700/50">
						<div class="flex items-center gap-2 mb-3">
							<svg class="w-4 h-4 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
								<path stroke-linecap="round" stroke-linejoin="round" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
							</svg>
							<h3 class="text-[10px] font-bold uppercase tracking-wider text-amber-400">
								Key Highlights
							</h3>
						</div>
						<div class="space-y-3">
							{#each source.highlights as highlight}
								<div class="highlight-excerpt bg-amber-500/10 border border-amber-500/30 rounded-lg p-3">
									<p class="text-sm text-surface-200 leading-relaxed">
										{highlight}
									</p>
								</div>
							{/each}
						</div>
					</section>
				{/if}

				<!-- Content preview -->
				{#if source.content_preview || source.content}
					<section class="p-4 border-b border-surface-700/50">
						<h3 class="text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-3">
							Content Preview
						</h3>
						<div class="prose prose-sm prose-invert max-w-none">
							<p class="text-sm text-surface-300 leading-relaxed whitespace-pre-wrap">
								{source.content || source.content_preview}
							</p>
						</div>
					</section>
				{/if}

				<!-- Metadata -->
				{#if source.metadata && Object.keys(source.metadata).length > 0}
					<section class="p-4">
						<h3 class="text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-3">
							Source Details
						</h3>
						<dl class="space-y-2">
							{#if source.metadata.collection}
								<div class="flex justify-between text-sm">
									<dt class="text-surface-500">Collection</dt>
									<dd class="text-surface-300">{source.metadata.collection}</dd>
								</div>
							{/if}
							{#if source.metadata.similarity_score != null}
								<div class="flex justify-between text-sm">
									<dt class="text-surface-500">Similarity Score</dt>
									<dd class="text-surface-300">{formatScore(source.metadata.similarity_score)}</dd>
								</div>
							{/if}
							{#if source.metadata.rerank_score != null}
								<div class="flex justify-between text-sm">
									<dt class="text-surface-500">Rerank Score</dt>
									<dd class="text-surface-300">{Number(source.metadata.rerank_score).toFixed(3)}</dd>
								</div>
							{/if}
							{#if source.metadata.published_date}
								<div class="flex justify-between text-sm">
									<dt class="text-surface-500">Published</dt>
									<dd class="text-surface-300">{source.metadata.published_date}</dd>
								</div>
							{/if}
						</dl>
					</section>
				{/if}
			</div>

			<!-- Footer -->
			<footer class="flex-shrink-0 p-4 border-t border-surface-700/50 bg-surface-900">
				<div class="flex gap-3">
					<button type="button" class="btn btn-default flex-1" onclick={onClose}>
						Close
					</button>
					{#if source.url}
						<a
							href={source.url}
							target="_blank"
							rel="noopener noreferrer"
							class="btn btn-primary flex-1 inline-flex items-center justify-center gap-2"
						>
							<span>Open Source</span>
							<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
								<path stroke-linecap="round" stroke-linejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
							</svg>
						</a>
					{/if}
				</div>
			</footer>
		</aside>
	</div>
{/if}

<style>
	@keyframes slide-in {
		from {
			transform: translateX(100%);
			opacity: 0;
		}
		to {
			transform: translateX(0);
			opacity: 1;
		}
	}

	.animate-slide-in {
		animation: slide-in 0.2s ease-out;
	}

	:global(.highlight-excerpt) {
		position: relative;
		transition: all 0.2s ease;
	}

	:global(.highlight-excerpt:hover) {
		background: rgba(251, 191, 36, 0.15);
		border-color: rgba(251, 191, 36, 0.4);
		transform: translateY(-1px);
	}
</style>
