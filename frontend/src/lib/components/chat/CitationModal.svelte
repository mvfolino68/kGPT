<script lang="ts">
	import { Button, Icon, IconButton, Backdrop } from '$lib/components/ui';
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
	<Backdrop onClose={onClose} class="z-50 bg-black/60" />

	<!-- Modal content container -->
	<div class="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
		<!-- Modal content -->
		<div class="w-full max-w-lg animate-fade-in pointer-events-auto">
			<div class="bg-surface-900 rounded-lg overflow-hidden shadow-2xl">
				<!-- Header -->
				<div class="px-4 py-3 flex items-center justify-between bg-surface-800">
					<div class="flex items-center gap-3">
						<span class="flex items-center justify-center w-6 h-6 rounded bg-surface-700/50 text-xs text-surface-200 font-bold">
							{index}
						</span>
						<div class="flex items-center gap-2">
							{#if citation.type === 'web'}
								<svg class="w-4 h-4 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
									<path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
								</svg>
								<span class="text-[10px] font-bold uppercase tracking-wider text-cyan-400">Web Source</span>
							{:else}
								<svg class="w-4 h-4 text-primary-light" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
									<path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
								</svg>
								<span class="text-[10px] font-bold uppercase tracking-wider text-primary-light">Documentation</span>
							{/if}
						</div>
					</div>
					<IconButton
						variant="ghost"
						size="sm"
						class="text-surface-400 hover:text-surface-200 hover:bg-surface-700"
						onclick={onClose}
						ariaLabel="Close modal"
						title="Close"
					>
						<Icon name="close" size="sm" strokeWidth={2} />
					</IconButton>
				</div>

				<!-- Body -->
				<div class="px-4 py-4 space-y-3">
					<div>
						<h3 class="text-sm font-semibold text-surface-100 mb-1 line-clamp-2">
							{citation.title}
						</h3>
						<p class="text-xs text-surface-500">
							{extractDomain(citation.url)}
						</p>
					</div>

					{#if citation.content_preview}
						<div class="p-3 rounded-lg bg-surface-700/40">
							<p class="text-xs text-surface-300 leading-relaxed line-clamp-6">
								{citation.content_preview}
							</p>
						</div>
					{/if}
				</div>

				<!-- Footer -->
				<div class="px-4 py-3 bg-surface-800 flex justify-end gap-2">
					<Button variant="ghost" size="sm" onclick={onClose}>
						Close
					</Button>
					{#if citation.url}
						<a
							href={citation.url}
							target="_blank"
							rel="noopener noreferrer"
							class="inline-flex items-center justify-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md bg-primary-700 text-white hover:bg-primary-800 transition-colors"
						>
							<span>Open Source</span>
							<Icon name="external" size="xs" strokeWidth={2} />
						</a>
					{/if}
				</div>
			</div>
		</div>
		</div>
	</div>
{/if}

<style>
	.line-clamp-2 {
		display: -webkit-box;
		line-clamp: 2;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
	.line-clamp-6 {
		display: -webkit-box;
		line-clamp: 6;
		-webkit-line-clamp: 6;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
</style>
