<script lang="ts">
	import { Card } from '$lib/components/ui';
	import type { MemberInfo, CoordinatorInfo } from './types';
	import OperationHeader from './OperationHeader.svelte';

	interface Props {
		groupId: string;
		state?: string;
		protocol?: string;
		coordinator?: CoordinatorInfo;
		members?: MemberInfo[];
	}

	let { groupId, state, protocol, coordinator, members = [] }: Props = $props();
</script>

<Card>
	<OperationHeader
		icon="groups"
		title="Group: {groupId}"
		subtitle="State: {state || 'Unknown'} | {members.length} members"
		color="cyan"
	/>

	<div class="space-y-2 mb-4">
		<div class="flex items-center justify-between text-xs bg-surface-800/40 rounded px-3 py-2">
			<span class="text-surface-400">Protocol</span>
			<span class="text-cyan-400 font-mono">{protocol || 'N/A'}</span>
		</div>
		<div class="flex items-center justify-between text-xs bg-surface-800/40 rounded px-3 py-2">
			<span class="text-surface-400">Coordinator</span>
			<span class="text-cyan-400 font-mono">
				{coordinator?.host || 'N/A'}{coordinator?.port ? `:${coordinator.port}` : ''}
			</span>
		</div>
	</div>

	{#if members.length > 0}
		<div>
			<h4 class="text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-2">
				Members
			</h4>
			<div class="space-y-2">
				{#each members as member}
					<div class="bg-surface-800/40 rounded p-2.5 text-xs border border-surface-700/30">
						<div class="text-cyan-400 font-medium">{member.client_id}</div>
						<div class="text-surface-500 mt-0.5">{member.host}</div>
					</div>
				{/each}
			</div>
		</div>
	{/if}
</Card>

