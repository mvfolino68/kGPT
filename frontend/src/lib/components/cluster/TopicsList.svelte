<script lang="ts">
	import { Card, Badge } from '$lib/components/ui';

	interface Props {
		topics: string[];
		maxDisplay?: number;
		onTopicClick?: (topic: string) => void;
	}

	let { topics, maxDisplay = 10, onTopicClick }: Props = $props();

	let showAll = $state(false);

	const displayedTopics = $derived(showAll ? topics : topics.slice(0, maxDisplay));
	const hasMore = $derived(topics.length > maxDisplay);
</script>

<Card>
	<div class="flex items-center justify-between mb-4">
		<h3 class="text-sm font-semibold text-surface-200">Topics</h3>
		<Badge variant="default">{topics.length}</Badge>
	</div>

	{#if topics.length === 0}
		<p class="text-sm text-surface-500 py-4 text-center">No topics found</p>
	{:else}
		<div class="space-y-1">
			{#each displayedTopics as topic}
				<button
					type="button"
					class="w-full text-left px-3 py-2 rounded-md text-sm font-mono text-surface-300 hover:bg-surface-700/50 hover:text-surface-100 transition-colors truncate"
					onclick={() => onTopicClick?.(topic)}
					title={topic}
				>
					{topic}
				</button>
			{/each}
		</div>

		{#if hasMore}
			<button
				type="button"
				class="w-full mt-3 py-2 text-sm text-primary-light hover:text-primary transition-colors"
				onclick={() => showAll = !showAll}
			>
				{showAll ? 'Show less' : `Show ${topics.length - maxDisplay} more`}
			</button>
		{/if}
	{/if}
</Card>
