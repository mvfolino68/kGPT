<script lang="ts">
	import { deleteTopic, type TopicInfo } from '$lib/api';
	import { educationalStore } from '$lib/stores/educational.svelte';
	import { Input, Select, Button, Card, Icon, ListItem } from '$lib/components/ui';

	interface Props {
		topics: TopicInfo[];
		onTopicClick?: (topic: string) => void;
	}

	let { topics = [], onTopicClick }: Props = $props();

	let searchQuery = $state('');
	let sortBy = $state('name');
	let showInternalTopics = $state(false);

	const sortOptions = [
		{ value: 'name', label: 'Name' },
		{ value: 'partitions', label: 'Partitions' },
		{ value: 'rf', label: 'RF' }
	];

	let userTopicsCount = $derived(topics.filter((t) => !t.is_internal).length);
	let internalTopicsCount = $derived(topics.filter((t) => t.is_internal).length);

	function filteredTopics() {
		let result = topics;

		// Filter internal
		if (!showInternalTopics) {
			result = result.filter((t) => !t.is_internal);
		}

		// Filter search
		if (searchQuery) {
			const q = searchQuery.toLowerCase();
			result = result.filter((t) => t.name.toLowerCase().includes(q));
		}

		// Sort
		return result.toSorted((a, b) => {
			if (sortBy === 'partitions') return b.partition_count - a.partition_count;
			if (sortBy === 'rf') return b.replication_factor - a.replication_factor;
			return a.name.localeCompare(b.name);
		});
	}

	function getReplicationBadgeClass(rf: number) {
		if (rf < 3) return 'bg-warning/20 text-warning';
		return 'bg-success/20 text-success';
	}

	async function handleDelete(topicName: string) {
		await educationalStore.performAction({
			type: 'delete',
			resource: 'topic',
			name: topicName,
			protocolOperation: 'DeleteTopics',
			explanation: `This will permanently delete the topic "${topicName}" and all of its messages.`,
			details: { topic: topicName },
			onConfirm: async () => {
				await deleteTopic(topicName);
				window.location.reload();
			}
		});
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
					<div class="col-span-12 sm:col-span-5">Topic</div>
					<div class="col-span-2 text-center hidden sm:block">Partitions</div>
					<div class="col-span-2 text-center hidden sm:block">RF</div>
					<div class="col-span-2 text-center">Status</div>
					<div class="col-span-1 text-right"></div>
				</div>

				<!-- Grid rows -->
				{#each filteredTopics() as topic}
					<ListItem
						class="grid grid-cols-12 gap-2 items-center"
						onclick={() => onTopicClick?.(topic.name)}
					>
						<div class="col-span-12 sm:col-span-5 flex items-center gap-2 min-w-0">
							{#if topic.is_internal}
								<span class="text-[10px] text-text-tertiary shrink-0">_</span>
							{/if}
							<span class="text-sm font-mono text-text truncate" title={topic.name}>
								{topic.name}
							</span>
						</div>
						<div class="col-span-2 text-center hidden sm:block">
							<span class="text-sm text-text-secondary tabular-nums">{topic.partition_count}</span>
						</div>
						<div class="col-span-2 text-center hidden sm:block">
							<span
								class="inline-flex items-center px-1.5 py-0.5 text-xs font-medium rounded {getReplicationBadgeClass(topic.replication_factor)}"
							>
								{topic.replication_factor}
							</span>
						</div>
						<div class="col-span-2 text-center flex justify-center">
							{#if topic.under_replicated}
								<span class="inline-flex items-center gap-1 text-xs text-warning" title="Under-replicated partitions">
									<Icon name="warning" size="xs" />
								</span>
							{:else}
								<span class="w-2.5 h-2.5 inline-block rounded-full bg-success shadow-[0_0_6px_rgba(52,211,153,0.5)]"></span>
							{/if}
						</div>
						<div class="col-span-1 text-right flex gap-1 justify-end">
							<Button
								variant="ghost"
								size="icon-sm"
								class="text-text-tertiary hover:text-primary hover:bg-primary/10 w-6 h-6"
								onclick={(e) => {
									e.stopPropagation();

									educationalStore.performAction({
										type: 'inspect',
										resource: 'topic',
										name: topic.name,
										protocolOperation: 'DescribeTopics',
										explanation: `Fetch detailed metadata and configuration for topic "${topic.name}".`,
										details: { topic: topic.name },
										onConfirm: async () => {
											// Trigger the "open details" flow which is currently just the onTopicClick
											// In a real app this might be distinct, but for now this matches "Inspect" intent
											onTopicClick?.(topic.name);
										}
									});
								}}
								title="Inspect topic"
							>
								<Icon name="eye" size="xs" />
							</Button>
							<Button
								variant="ghost"
								size="icon-sm"
								class="text-text-tertiary hover:text-error hover:bg-error/10 w-6 h-6"
								onclick={(e) => {
									e.stopPropagation();
									handleDelete(topic.name);
								}}
								title="Delete topic"
							>
								<Icon name="trash" size="xs" />
							</Button>
						</div>
					</ListItem>
				{/each}
			{/if}
		</div>
	{/snippet}
</Card>
