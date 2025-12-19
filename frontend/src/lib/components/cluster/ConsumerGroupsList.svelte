<script lang="ts">
	interface Props {
		groups: string[];
		maxDisplay?: number;
		onGroupClick?: (group: string) => void;
	}

	let { groups, maxDisplay = 10, onGroupClick }: Props = $props();

	let showAll = $state(false);

	const displayedGroups = $derived(showAll ? groups : groups.slice(0, maxDisplay));
	const hasMore = $derived(groups.length > maxDisplay);
</script>

<div class="bg-surface-800 rounded-lg overflow-hidden">
	<div class="px-4 py-3 flex items-center justify-between">
		<h3 class="text-[10px] font-bold uppercase tracking-wider text-surface-500">Consumer Groups</h3>
		<span class="px-2 py-0.5 text-xs bg-surface-700/50 text-surface-400 rounded">
			{groups.length}
		</span>
	</div>

	<div class="p-2">
		{#if groups.length === 0}
			<p class="text-sm text-surface-500 py-4 text-center">No consumer groups found</p>
		{:else}
			<div class="space-y-0.5">
				{#each displayedGroups as group}
					<button
						type="button"
						class="w-full text-left px-3 py-2 rounded text-sm font-mono text-surface-300 hover:bg-surface-800/50 hover:text-surface-100 transition-colors truncate"
						onclick={() => onGroupClick?.(group)}
						title={group}
					>
						{group}
					</button>
				{/each}
			</div>

			{#if hasMore}
				<button
					type="button"
					class="w-full mt-2 py-2 text-sm text-surface-400 hover:text-surface-200 transition-colors"
					onclick={() => showAll = !showAll}
				>
					{showAll ? 'Show less' : `Show ${groups.length - maxDisplay} more`}
				</button>
			{/if}
		{/if}
	</div>
</div>
