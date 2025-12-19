<script lang="ts">
	interface Props {
		topics: string[];
		maxVisible?: number;
	}

	let { topics, maxVisible = 24 }: Props = $props();
</script>

<div class="pt-4 border-t border-surface-700/50">
	<div class="flex items-center gap-2 mb-3">
		<span class="text-[10px] font-bold text-surface-500 uppercase tracking-wider">Topics</span>
		<span class="text-xs text-surface-600">[{topics.length}]</span>
	</div>
	<div class="flex flex-wrap gap-1.5">
		{#each topics.slice(0, maxVisible) as topic}
			<span class="px-2.5 py-1 text-xs bg-surface-800/50 border border-surface-700/50 rounded">
				{topic}
			</span>
		{/each}
		{#if topics.length > maxVisible}
			<span class="px-2.5 py-1 text-xs bg-surface-800/60 text-surface-500 rounded border border-surface-700">
				+{topics.length - maxVisible} more
			</span>
		{/if}
	</div>
</div>

