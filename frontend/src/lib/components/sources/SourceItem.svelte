<script lang="ts">
	import type { Source } from './types';

	interface Props {
		source: Source;
		index: number;
		isExpanded?: boolean;
		onSelect: (source: Source) => void;
	}

	let { source, index, isExpanded = false, onSelect }: Props = $props();

	function getTypeConfig(type: Source['type']) {
		switch (type) {
			case 'doc':
				return {
					label: 'Documentation',
					color: 'text-blue-400',
					bg: 'bg-blue-500/10',
					border: 'border-blue-500/20',
					icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z'
				};
			case 'web':
				return {
					label: 'Web',
					color: 'text-blue-400',
					bg: 'bg-blue-500/10',
					border: 'border-blue-500/20',
					icon: 'M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9'
				};
			case 'cluster':
				return {
					label: 'Cluster',
					color: 'text-amber-400',
					bg: 'bg-amber-500/10',
					border: 'border-amber-500/20',
					icon: 'M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01'
				};
			default:
				return {
					label: 'Source',
					color: 'text-surface-400',
					bg: 'bg-surface-500/10',
					border: 'border-surface-500/20',
					icon: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
				};
		}
	}

	function extractDomain(url: string): string {
		if (!url) return '';
		try {
			return new URL(url).hostname.replace('www.', '');
		} catch {
			return url.split('/')[0] || '';
		}
	}

	function formatScore(score: number | undefined): string {
		if (score === undefined) return '';
		return `${Math.round(score * 100)}%`;
	}

	const typeConfig = $derived(getTypeConfig(source.type));
</script>

<button
	type="button"
	class="w-full text-left group"
	onclick={() => onSelect(source)}
>
	<div class="flex items-start gap-3 p-3 rounded-lg transition-all duration-150
		bg-surface-800/40 hover:bg-surface-800/70 border {typeConfig.border}
		hover:border-opacity-50 cursor-pointer">

		<!-- Index badge -->
		<div class="flex-shrink-0 w-5 h-5 rounded flex items-center justify-center
			{typeConfig.bg} {typeConfig.color} text-[10px] font-bold font-mono mt-0.5">
			{index}
		</div>

		<!-- Content -->
		<div class="flex-1 min-w-0 space-y-1.5">
			<!-- Title row -->
			<div class="flex items-start justify-between gap-2">
				<h4 class="text-sm font-medium text-surface-100 leading-snug line-clamp-2
					group-hover:text-white transition-colors">
					{source.title}
				</h4>
				{#if source.relevance_score !== undefined}
					<span class="flex-shrink-0 text-[10px] font-mono {typeConfig.color}
						bg-surface-900/60 px-1.5 py-0.5 rounded">
						{formatScore(source.relevance_score)}
					</span>
				{/if}
			</div>

			<!-- URL / Domain -->
			{#if source.url}
				<div class="flex items-center gap-1.5 text-[11px] text-surface-500">
					<svg class="w-3 h-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
					</svg>
					<span class="truncate font-mono">{extractDomain(source.url)}</span>
				</div>
			{/if}

			<!-- Preview text -->
			{#if source.content_preview && isExpanded}
				<p class="text-xs text-surface-400 leading-relaxed line-clamp-3 mt-2">
					{source.content_preview}
				</p>
			{/if}

			<!-- Type badge -->
			<div class="flex items-center gap-1.5 pt-1">
				<div class="flex items-center gap-1 {typeConfig.bg} {typeConfig.color}
					px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider">
					<svg class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d={typeConfig.icon} />
					</svg>
					{typeConfig.label}
				</div>
				{#if source.metadata?.collection}
					<span class="text-[9px] text-surface-600 font-mono">
						{source.metadata.collection}
					</span>
				{/if}
			</div>
		</div>

		<!-- Expand indicator -->
		<svg class="w-4 h-4 text-surface-600 group-hover:text-surface-400
			transition-colors flex-shrink-0 mt-0.5"
			fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
			<path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
		</svg>
	</div>
</button>

<style>
	.line-clamp-2 {
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
	.line-clamp-3 {
		display: -webkit-box;
		-webkit-line-clamp: 3;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
</style>
