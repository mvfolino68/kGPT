<script lang="ts">
	import type { ConsumerGroupInfo } from '$lib/api';
	import { ListItem } from '$lib/components/ui';

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
		if (s.includes('stable')) return 'bg-emerald-500/10 text-emerald-400';
		if (s.includes('empty')) return 'bg-surface-600/50 text-surface-400';
		if (s.includes('preparing') || s.includes('completing'))
			return 'bg-amber-500/10 text-amber-400';
		if (s.includes('dead')) return 'bg-red-500/10 text-red-400';
		return 'bg-surface-600/50 text-surface-400';
	}

	function formatState(state: string): string {
		// Clean up state string like "ConsumerGroupState.STABLE" -> "Stable"
		const parts = state.split('.');
		const stateName = parts[parts.length - 1];
		return stateName.charAt(0).toUpperCase() + stateName.slice(1).toLowerCase();
	}
</script>

<div class="panel overflow-hidden">
	<!-- Header -->
	<div class="panel-header space-y-3">
		<div class="flex items-center justify-between">
			<h3 class="text-sm font-medium text-surface-200">Consumer Groups</h3>
			<span class="text-xs text-surface-500">{groups.length} groups</span>
		</div>

		{#if groups.length > 0}
			<div class="relative">
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
					placeholder="Search groups..."
					bind:value={searchQuery}
					class="input w-full pl-9 pr-3 py-1.5 text-sm"
				/>
			</div>
		{/if}
	</div>

	<!-- Groups list -->
	<div class="max-h-80 overflow-y-auto">
		{#if filteredGroups().length === 0}
			<div class="p-8 text-center">
				{#if groups.length === 0}
					<svg
						class="w-10 h-10 mx-auto text-surface-600 mb-3"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
						stroke-width="1"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M18 18.72a9.094 9.094 0 003.741-.479 3 3 0 00-4.682-2.72m.94 3.198l.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0112 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 016 18.719m12 0a5.971 5.971 0 00-.941-3.197m0 0A5.995 5.995 0 0012 12.75a5.995 5.995 0 00-5.058 2.772m0 0a3 3 0 00-4.681 2.72 8.986 8.986 0 003.74.477m.94-3.197a5.971 5.971 0 00-.94 3.197M15 6.75a3 3 0 11-6 0 3 3 0 016 0zm6 3a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0zm-13.5 0a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z"
						/>
					</svg>
					<p class="text-sm text-surface-500">No consumer groups</p>
					<p class="text-xs text-surface-600 mt-1">Groups appear when consumers connect</p>
				{:else}
					<p class="text-sm text-surface-500">No groups match your search</p>
				{/if}
			</div>
		{:else}
			<div>
				{#each filteredGroups() as group}
					<ListItem
						class="py-3"
						onclick={() => onGroupClick?.(group.group_id)}
					>
						<div class="flex items-start justify-between gap-4">
							<div class="min-w-0 flex-1">
								<div class="flex items-center gap-2 mb-1">
									<span
										class="text-sm font-mono text-surface-200 truncate"
										title={group.group_id}
									>
										{group.group_id}
									</span>
									<span
										class="shrink-0 px-1.5 py-0.5 text-[10px] font-medium rounded {getStateBadgeClass(
											group.state
										)}"
									>
										{formatState(group.state)}
									</span>
								</div>

								<div class="flex items-center gap-4 text-xs text-surface-500">
									{#if group.member_count > 0}
										<span class="flex items-center gap-1">
											<svg
												class="w-3.5 h-3.5"
												fill="none"
												stroke="currentColor"
												viewBox="0 0 24 24"
												stroke-width="1.5"
											>
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z"
												/>
											</svg>
											{group.member_count} members
										</span>
									{/if}

									{#if group.coordinator_id !== null}
										<span>Coordinator: B{group.coordinator_id}</span>
									{/if}

									{#if group.protocol_type}
										<span class="text-surface-600">{group.protocol_type}</span>
									{/if}
								</div>

								{#if group.topics.length > 0}
									<div class="mt-2 flex items-center gap-1.5 flex-wrap">
										{#each group.topics.slice(0, 3) as topic}
											<span
												class="px-1.5 py-0.5 text-[10px] bg-surface-700/50 text-surface-400 rounded font-mono"
											>
												{topic}
											</span>
										{/each}
										{#if group.topics.length > 3}
											<span class="text-[10px] text-surface-600">
												+{group.topics.length - 3} more
											</span>
										{/if}
									</div>
								{/if}
							</div>

							<svg
								class="w-4 h-4 text-surface-600 shrink-0 mt-0.5"
								fill="none"
								stroke="currentColor"
								viewBox="0 0 24 24"
								stroke-width="1.5"
							>
								<path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
							</svg>
						</div>
					</ListItem>
				{/each}
			</div>
		{/if}
	</div>
</div>
