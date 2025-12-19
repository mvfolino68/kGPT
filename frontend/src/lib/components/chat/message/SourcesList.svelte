<script lang="ts">
	import type { Source } from '$lib/components/sources/types';
	import { Button } from '$lib/components/ui';

	interface Props {
		sources: Source[];
		onSourceClick: (source: Source) => void;
	}

	let { sources, onSourceClick }: Props = $props();

	let expanded = $state(false);
</script>

{#if sources.length > 0}
	<div class="mt-3 pt-3">
		<Button
			variant="ghost"
			size="xs"
			class="px-0 py-0 text-xs text-surface-400 hover:text-cyan-400 hover:bg-transparent"
			onclick={() => expanded = !expanded}
		>
			<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
				<path stroke-linecap="round" stroke-linejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
			</svg>
			<span>{sources.length} {sources.length === 1 ? 'Source' : 'Sources'}</span>
			<svg
				class="w-3 h-3 transition-transform duration-200 {expanded ? 'rotate-180' : ''}"
				fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"
			>
				<path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
			</svg>
		</Button>

		{#if expanded}
			<ul class="mt-2 space-y-1">
				{#each sources as source, i}
					<li>
						<Button
							variant="ghost"
							size="sm"
							class="w-full justify-start text-left px-2 py-1.5 rounded text-xs text-surface-300 hover:text-cyan-400 hover:bg-surface-800/50"
							onclick={() => onSourceClick(source)}
						>
							<span class="text-cyan-500/70">[{i + 1}]</span>
							<span class="truncate">{source.title}</span>
						</Button>
					</li>
				{/each}
			</ul>
		{/if}
	</div>
{/if}

