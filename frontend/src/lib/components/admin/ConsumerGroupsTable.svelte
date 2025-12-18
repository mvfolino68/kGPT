<script lang="ts">
	import type { GroupInfo } from './types';
	import OperationHeader from './OperationHeader.svelte';
	import DataTable from './DataTable.svelte';

	interface Props {
		groups: (string | GroupInfo)[];
		totalCount?: number;
	}

	let { groups, totalCount }: Props = $props();

	const displayGroups = $derived(groups.slice(0, 20));
	const count = $derived(totalCount || groups.length);
</script>

<div class="bg-surface-900 border border-surface-700/50 rounded-lg p-4">
	<OperationHeader
		icon="groups"
		title="Consumer Groups"
		subtitle="{count} total"
		color="cyan"
	/>

	{#if groups.length > 0}
		<DataTable headers={['Group ID', 'State']} maxRows={20} totalCount={groups.length}>
			{#each displayGroups as group}
				<tr class="border-b border-surface-700/30 last:border-b-0 hover:bg-surface-800/60 transition-colors">
					<td class="px-3 py-2 text-cyan-400">
						{typeof group === 'string' ? group : group.group_id}
					</td>
					<td class="px-3 py-2 text-right text-surface-300">
						{typeof group === 'object' && group.state ? group.state : '-'}
					</td>
				</tr>
			{/each}
		</DataTable>
	{:else}
		<p class="text-sm text-surface-400">No consumer groups found.</p>
	{/if}
</div>
