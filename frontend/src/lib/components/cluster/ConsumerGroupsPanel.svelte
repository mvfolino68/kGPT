<script lang="ts">
	import type { ConsumerGroupInfo } from '$lib/api';
	import { ListItem, Card, Input, Icon } from '$lib/components/ui';

	interface Props {
		groups: ConsumerGroupInfo[];
		onGroupClick?: (groupId: string) => void;
	}

	let { groups, onGroupClick }: Props = $props();

	let searchQuery = $state('');

	const filteredGroups = $derived(() => {
		if (!searchQuery) return groups;
		return groups.filter((g) => g.group_id.toLowerCase().includes(searchQuery.toLowerCase()));
	});

	function getStateBadgeClass(state: string): string {
		const s = state.toLowerCase();
		if (s.includes('stable')) return 'bg-success/10 text-success';
		if (s.includes('empty')) return 'bg-surface-hover text-text-tertiary';
		if (s.includes('preparing') || s.includes('completing')) return 'bg-warning/10 text-warning';
		if (s.includes('dead')) return 'bg-error/10 text-error';
		return 'bg-surface-hover text-text-tertiary';
	}

	function formatState(state: string): string {
		const parts = state.split('.');
		const stateName = parts[parts.length - 1];
		return stateName.charAt(0).toUpperCase() + stateName.slice(1).toLowerCase();
	}
</script>

<Card title="Consumer Groups" subtitle="{groups.length} groups">
	{#snippet children()}
		<div class="space-y-3">
			{#if groups.length > 0}
				<Input
					type="text"
					placeholder="Search groups..."
					bind:value={searchQuery}
				>
					{#snippet icon()}
						<Icon name="search" size="sm" />
					{/snippet}
				</Input>
			{/if}
		</div>

		<!-- Groups list -->
		<div class="max-h-80 overflow-y-auto mt-3">
			{#if filteredGroups().length === 0}
				<div class="p-8 text-center">
					{#if groups.length === 0}
						<Icon name="users" size="xl" class="mx-auto text-text-tertiary mb-3 w-10 h-10" />
						<p class="text-sm text-text-tertiary">No consumer groups</p>
						<p class="text-xs text-text-tertiary mt-1">Groups appear when consumers connect</p>
					{:else}
						<p class="text-sm text-text-tertiary">No groups match your search</p>
					{/if}
				</div>
			{:else}
				<div>
					{#each filteredGroups() as group}
						<ListItem class="py-3" onclick={() => onGroupClick?.(group.group_id)}>
							<div class="flex items-start justify-between gap-4">
								<div class="min-w-0 flex-1">
									<div class="flex items-center gap-2 mb-1">
										<span class="text-sm font-mono text-text truncate" title={group.group_id}>
											{group.group_id}
										</span>
										<span class="shrink-0 px-1.5 py-0.5 text-[10px] font-medium rounded {getStateBadgeClass(group.state)}">
											{formatState(group.state)}
										</span>
									</div>

									<div class="flex items-center gap-4 text-xs text-text-tertiary">
										{#if group.member_count > 0}
											<span class="flex items-center gap-1">
												<Icon name="users" size="xs" />
												{group.member_count} members
											</span>
										{/if}

										{#if group.coordinator_id !== null}
											<span>Coordinator: B{group.coordinator_id}</span>
										{/if}

										{#if group.protocol_type}
											<span class="text-text-tertiary">{group.protocol_type}</span>
										{/if}
									</div>

									{#if group.topics.length > 0}
										<div class="mt-2 flex items-center gap-1.5 flex-wrap">
											{#each group.topics.slice(0, 3) as topic}
												<span class="px-1.5 py-0.5 text-[10px] bg-surface-hover text-text-tertiary rounded font-mono">
													{topic}
												</span>
											{/each}
											{#if group.topics.length > 3}
												<span class="text-[10px] text-text-tertiary">
													+{group.topics.length - 3} more
												</span>
											{/if}
										</div>
									{/if}
								</div>

								<Icon name="chevron-right" size="sm" class="text-text-tertiary shrink-0 mt-0.5" />
							</div>
						</ListItem>
					{/each}
				</div>
			{/if}
		</div>
	{/snippet}
</Card>
