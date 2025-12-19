<script lang="ts">
	import type { TopicInfo } from '$lib/api';
	import { ListItem, Button, Card, Input, Select, Icon } from '$lib/components/ui';

	interface Props {
		topics: TopicInfo[];
		onTopicClick?: (topicName: string) => void;
		showInternal?: boolean;
	}

	let { topics, onTopicClick, showInternal = false }: Props = $props();

	let searchQuery = $state('');
	let sortBy = $state<'name' | 'partitions' | 'replication'>('name');
	let showInternalTopics = $state(false);

	$effect(() => {
		showInternalTopics = showInternal;
	});

	const sortOptions = [
		{ value: 'name', label: 'Name' },
		{ value: 'partitions', label: 'Partitions' },
		{ value: 'replication', label: 'Replication' }
	];

	const filteredTopics = $derived(() => {
		let filtered = topics.filter((t) => {
			if (!showInternalTopics && t.is_internal) return false;
			if (searchQuery && !t.name.toLowerCase().includes(searchQuery.toLowerCase())) return false;
			return true;
		});

		filtered.sort((a, b) => {
			if (sortBy === 'partitions') return b.partition_count - a.partition_count;
			if (sortBy === 'replication') return b.replication_factor - a.replication_factor;
			return a.name.localeCompare(b.name);
		});

		return filtered;
	});

	const userTopicsCount = $derived(topics.filter((t) => !t.is_internal).length);
	const internalTopicsCount = $derived(topics.filter((t) => t.is_internal).length);

	function getReplicationBadgeClass(rf: number): string {
		if (rf >= 3) return 'bg-success/10 text-success';
		if (rf === 2) return 'bg-warning/10 text-warning';
		return 'bg-error/10 text-error';
	}
</script>

<Card title="Topics" subtitle="{userTopicsCount} user | {internalTopicsCount} internal">
	{#snippet children()}
		<div class="space-y-3">
			<div class="flex items-center gap-2">
				<div class="flex-1">
					<Input
						type="text"
						placeholder="Search topics..."
						bind:value={searchQuery}
					>
						{#snippet icon()}
							<Icon name="search" size="sm" />
						{/snippet}
					</Input>
				</div>

				<Select bind:value={sortBy} options={sortOptions} class="w-28" />

				<Button
					variant="ghost"
					size="sm"
					class={showInternalTopics ? 'bg-primary/20 text-primary' : ''}
					onclick={() => (showInternalTopics = !showInternalTopics)}
				>
					Internal
				</Button>
			</div>
		</div>

		<!-- Topics list -->
		<div class="max-h-80 overflow-y-auto mt-3">
			{#if filteredTopics().length === 0}
				<div class="p-6 text-center text-text-tertiary text-sm">
					{searchQuery ? 'No topics match your search' : 'No topics found'}
				</div>
			{:else}
				<!-- Grid header -->
				<div class="grid grid-cols-12 gap-2 px-4 py-2 bg-bg-elevated rounded-md text-[10px] font-bold uppercase tracking-wider text-text-tertiary sticky top-0">
					<div class="col-span-6">Topic</div>
					<div class="col-span-2 text-center">Partitions</div>
					<div class="col-span-2 text-center">RF</div>
					<div class="col-span-2 text-right">Status</div>
				</div>

				<!-- Grid rows -->
				{#each filteredTopics() as topic}
					<ListItem
						class="grid grid-cols-12 gap-2 items-center"
						onclick={() => onTopicClick?.(topic.name)}
					>
						<div class="col-span-6 flex items-center gap-2 min-w-0">
							{#if topic.is_internal}
								<span class="text-[10px] text-text-tertiary shrink-0">_</span>
							{/if}
							<span class="text-sm font-mono text-text truncate" title={topic.name}>
								{topic.name}
							</span>
						</div>
						<div class="col-span-2 text-center">
							<span class="text-sm text-text-secondary tabular-nums">{topic.partition_count}</span>
						</div>
						<div class="col-span-2 text-center">
							<span
								class="inline-flex items-center px-1.5 py-0.5 text-xs font-medium rounded {getReplicationBadgeClass(topic.replication_factor)}"
							>
								{topic.replication_factor}
							</span>
						</div>
						<div class="col-span-2 text-right">
							{#if topic.under_replicated}
								<span class="inline-flex items-center gap-1 text-xs text-warning" title="Under-replicated partitions">
									<Icon name="warning" size="xs" />
								</span>
							{:else}
								<span class="w-2.5 h-2.5 inline-block rounded-full bg-success shadow-[0_0_6px_rgba(52,211,153,0.5)]"></span>
							{/if}
						</div>
					</ListItem>
				{/each}
			{/if}
		</div>
	{/snippet}
</Card>
