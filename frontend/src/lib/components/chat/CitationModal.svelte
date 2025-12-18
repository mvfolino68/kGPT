<script lang="ts">
	import { RetroCard, RetroButton } from '$lib/components';
	import type { CitationObject } from '$lib/api';

	interface Props {
		citation: CitationObject | null;
		index: number;
		position?: { x: number; y: number };
		onClose: () => void;
	}

	let { citation, index, position, onClose }: Props = $props();

	function extractDomain(url: string): string {
		if (!url) return 'Unknown';
		try {
			return new URL(url).hostname.replace('www.', '');
		} catch {
			return url.split('/')[0] || url;
		}
	}

	function handleBackdropClick(event: MouseEvent) {
		if (event.target === event.currentTarget) {
			onClose();
		}
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') {
			onClose();
		}
	}
</script>

<svelte:window on:keydown={handleKeydown} />

{#if citation}
	<!-- Modal backdrop -->
	<div
		class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
		role="button"
		tabindex="-1"
		onclick={handleBackdropClick}
		onkeydown={(e) => e.key === 'Enter' && onClose()}
	>
		<!-- Modal content -->
		<div class="w-full max-w-lg animate-scale-in">
			<RetroCard variant={citation.type === 'web' ? 'glow-cyan' : 'glow-blue'} class="!p-0">
				<!-- Header -->
				<div class="px-4 py-3 border-b border-surface-700 flex items-center justify-between">
					<div class="flex items-center gap-3">
						<span class="flex items-center justify-center w-6 h-6 rounded bg-surface-800 text-xs font-mono text-blue-400 font-bold">
							{index}
						</span>
						<div class="flex items-center gap-2">
							{#if citation.type === 'web'}
								<svg class="w-4 h-4 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
									<path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
								</svg>
								<span class="text-[10px] font-mono text-cyan-400 uppercase tracking-wider">Web Source</span>
							{:else}
								<svg class="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
									<path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
								</svg>
								<span class="text-[10px] font-mono text-blue-400 uppercase tracking-wider">Documentation</span>
							{/if}
						</div>
					</div>
					<button
						type="button"
						class="p-1.5 rounded hover:bg-surface-700 transition-colors text-surface-400 hover:text-surface-200"
						onclick={onClose}
						aria-label="Close modal"
					>
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
						</svg>
					</button>
				</div>

				<!-- Body -->
				<div class="px-4 py-4 space-y-3">
					<div>
						<h3 class="text-sm font-semibold text-surface-100 mb-1 line-clamp-2">
							{citation.title}
						</h3>
						<p class="text-xs font-mono text-surface-500">
							{extractDomain(citation.url)}
						</p>
					</div>

					{#if citation.content_preview}
						<div class="p-3 rounded bg-surface-900/50 border border-surface-700">
							<p class="text-xs text-surface-300 leading-relaxed line-clamp-6">
								{citation.content_preview}
							</p>
						</div>
					{/if}
				</div>

				<!-- Footer -->
				<div class="px-4 py-3 border-t border-surface-700 flex justify-end gap-2">
					<RetroButton size="sm" onclick={onClose}>
						Close
					</RetroButton>
					{#if citation.url}
						<a
							href={citation.url}
							target="_blank"
							rel="noopener noreferrer"
							class="retro-button retro-button-sm retro-button-primary inline-flex items-center gap-1.5"
						>
							<span>Open Source</span>
							<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
								<path stroke-linecap="round" stroke-linejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
							</svg>
						</a>
					{/if}
				</div>
			</RetroCard>
		</div>
	</div>
{/if}

<style>
	.line-clamp-2 {
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
	.line-clamp-6 {
		display: -webkit-box;
		-webkit-line-clamp: 6;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
	@keyframes scale-in {
		from {
			opacity: 0;
			transform: scale(0.95);
		}
		to {
			opacity: 1;
			transform: scale(1);
		}
	}
	.animate-scale-in {
		animation: scale-in 0.15s ease-out;
	}
</style>
