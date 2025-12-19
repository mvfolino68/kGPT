<script lang="ts">
	import { formatConfigValue, type ConfigEntry } from './types';
	import { Button } from '$lib/components/ui';

	interface Props {
		config: Record<string, ConfigEntry>;
		color?: 'green' | 'cyan' | 'violet' | 'amber';
		initialShow?: number;
	}

	let { config, color = 'green', initialShow = 6 }: Props = $props();

	let showAll = $state(false);

	const entries = $derived(Object.entries(config));
	const displayEntries = $derived(showAll ? entries : entries.slice(0, initialShow));
	const hasMore = $derived(entries.length > initialShow);

	const colorClass = {
		green: 'text-emerald-400',
		cyan: 'text-cyan-400',
		violet: 'text-violet-400',
		amber: 'text-amber-400'
	};
</script>

{#if entries.length > 0}
	<div>
		<h4 class="text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-2">
			Configuration
		</h4>
		<div class="space-y-1.5">
			{#each displayEntries as [key, value]}
				<div class="flex items-center justify-between text-xs bg-surface-800/40 rounded px-2.5 py-1.5">
					<span class="text-surface-400 truncate max-w-[50%]">{key}</span>
					<span class="{colorClass[color]} font-mono truncate max-w-[45%]">
						{formatConfigValue(value)}
					</span>
				</div>
			{/each}
			{#if hasMore}
				<Button
					variant="ghost"
					size="xs"
					class="px-0 py-0 text-xs text-surface-500 hover:text-surface-300 hover:bg-transparent"
					onclick={() => showAll = !showAll}
				>
					{showAll ? 'Show less' : `Show ${entries.length - initialShow} more...`}
				</Button>
			{/if}
		</div>
	</div>
{/if}

