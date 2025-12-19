<script lang="ts">
	import type { TopicInfo } from '$lib/api';
	import { ListItem, Button } from '$lib/components/ui';

	interface Props {
		topics: TopicInfo[];
		onTopicClick?: (topicName: string) => void;
		showInternal?: boolean;
	}

	let { topics, onTopicClick, showInternal = false }: Props = $props();

	let searchQuery = $state('');
	let sortBy = $state<'name' | 'partitions' | 'replication'>('name');
	let showInternalTopics = $state(showInternal);

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
		if (rf >= 3) return 'bg-emerald-500/10 text-emerald-400';
		if (rf === 2) return 'bg-amber-500/10 text-amber-400';
		return 'bg-red-500/10 text-red-400';
	}
</script>

<div class="panel overflow-hidden">
	<!-- Header -->
	<div class="panel-header space-y-3">
		<div class="flex items-center justify-between">
			<h3 class="text-sm font-medium text-surface-200">Topics</h3>
			<div class="flex items-center gap-2 text-xs text-surface-500">
				<span>{userTopicsCount} user</span>
				<span class="text-surface-600">|</span>
				<span>{internalTopicsCount} internal</span>
			</div>
		</div>

		<div class="flex items-center gap-2">
			<div class="flex-1 relative">
				<svg
					class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-500"
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
					stroke-width="1.5"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
					/>
				</svg>
				<input
					type="text"
					placeholder="Search topics..."
					bind:value={searchQuery}
					class="input w-full pl-9 pr-3 py-1.5 text-sm"
				/>
			</div>

			<select bind:value={sortBy} class="input px-2 py-1.5 text-xs">
				<option value="name">Name</option>
				<option value="partitions">Partitions</option>
				<option value="replication">Replication</option>
			</select>

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
	<div class="max-h-80 overflow-y-auto">
		{#if filteredTopics().length === 0}
			<div class="p-6 text-center text-surface-500 text-sm">
				{searchQuery ? 'No topics match your search' : 'No topics found'}
			</div>
		{:else}
			<!-- Grid header -->
			<div class="grid grid-cols-12 gap-2 px-4 py-2 bg-surface-900/50 text-[10px] font-bold uppercase tracking-wider text-surface-500 sticky top-0">
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
							<span class="text-[10px] text-surface-600 shrink-0">_</span>
						{/if}
						<span class="text-sm font-mono text-surface-200 truncate" title={topic.name}>
							{topic.name}
						</span>
					</div>
					<div class="col-span-2 text-center">
						<span class="text-sm text-surface-300 tabular-nums">{topic.partition_count}</span>
					</div>
					<div class="col-span-2 text-center">
						<span
							class="inline-flex items-center px-1.5 py-0.5 text-xs font-medium rounded {getReplicationBadgeClass(
								topic.replication_factor
							)}"
						>
							{topic.replication_factor}
						</span>
					</div>
					<div class="col-span-2 text-right">
						{#if topic.under_replicated}
							<span
								class="inline-flex items-center gap-1 text-xs text-amber-400"
								title="Under-replicated partitions"
							>
								<svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
									<path
										fill-rule="evenodd"
										d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z"
										clip-rule="evenodd"
									/>
								</svg>
							</span>
						{:else}
							<span class="w-2 h-2 inline-block rounded-full bg-emerald-400/80"></span>
						{/if}
					</div>
				</ListItem>
			{/each}
		{/if}
	</div>
</div>
