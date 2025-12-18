<script lang="ts">
	import { Card, Badge } from '$lib/components/ui';

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

<Card>
	<div class="flex items-center justify-between mb-4">
		<h3 class="text-sm font-semibold text-surface-200">Consumer Groups</h3>
		<Badge variant="default">{groups.length}</Badge>
	</div>

	{#if groups.length === 0}
		<p class="text-sm text-surface-500 py-4 text-center">No consumer groups found</p>
	{:else}
		<div class="space-y-1">
			{#each displayedGroups as group}
				<button
					type="button"
					class="w-full text-left px-3 py-2 rounded-md text-sm font-mono text-surface-300 hover:bg-surface-700/50 hover:text-surface-100 transition-colors truncate"
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
				class="w-full mt-3 py-2 text-sm text-primary-light hover:text-primary transition-colors"
				onclick={() => showAll = !showAll}
			>
				{showAll ? 'Show less' : `Show ${groups.length - maxDisplay} more`}
			</button>
		{/if}
	{/if}
</Card>
