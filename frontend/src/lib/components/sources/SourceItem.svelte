<script lang="ts">
	import type { Source } from './types';
	import { ClickableCard, Icon, Badge } from '$lib/components/ui';

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
					variant: 'info' as const,
					icon: 'file-text'
				};
			case 'web':
				return {
					label: 'Web',
					variant: 'info' as const,
					icon: 'globe'
				};
			case 'cluster':
				return {
					label: 'Cluster',
					variant: 'warning' as const,
					icon: 'server'
				};
			default:
				return {
					label: 'Source',
					variant: 'default' as const,
					icon: 'link'
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

<ClickableCard
	variant="bordered"
	padding="sm"
	class="group"
	onclick={() => onSelect(source)}
>
	<div class="flex items-start gap-3">
		<!-- Index badge -->
		<Badge variant={typeConfig.variant} size="sm" class="mt-0.5 font-mono">
			{index}
		</Badge>

		<!-- Content -->
		<div class="flex-1 min-w-0 space-y-1.5">
			<!-- Title row -->
			<div class="flex items-start justify-between gap-2">
				<h4 class="text-sm font-medium text-surface-100 leading-snug line-clamp-2
					group-hover:text-white transition-colors">
					{source.title}
				</h4>
				{#if source.relevance_score !== undefined}
					<Badge variant="default" size="sm" class="font-mono bg-surface-900/60">
						{formatScore(source.relevance_score)}
					</Badge>
				{/if}
			</div>

			<!-- URL / Domain -->
			{#if source.url}
				<div class="flex items-center gap-1.5 text-[11px] text-surface-500">
					<Icon name="link" size="xs" class="flex-shrink-0" />
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
				<Badge variant={typeConfig.variant} size="sm" class="uppercase tracking-wider">
					<Icon name={typeConfig.icon} size="xs" />
					{typeConfig.label}
				</Badge>

				{#if source.highlights && source.highlights.length > 0}
					<Badge variant="warning" size="sm" class="font-mono">
						<Icon name="sparkles" size="xs" />
						{source.highlights.length}
					</Badge>
				{/if}
				{#if source.metadata?.collection}
					<span class="text-[9px] text-surface-600 font-mono">
						{source.metadata.collection}
					</span>
				{/if}
			</div>
		</div>

		<!-- Expand indicator -->
		<Icon name="chevron-right" size="sm" class="text-surface-600 group-hover:text-surface-400 transition-colors flex-shrink-0 mt-0.5" />
	</div>
</ClickableCard>

<style>
	.line-clamp-2 {
		display: -webkit-box;
		line-clamp: 2;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
	.line-clamp-3 {
		display: -webkit-box;
		line-clamp: 3;
		-webkit-line-clamp: 3;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
</style>
