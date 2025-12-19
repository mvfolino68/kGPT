<script lang="ts">
	interface Props {
		onAction: (action: string) => void;
		disabled?: boolean;
	}

	let { onAction, disabled = false }: Props = $props();

	const actions = [
		{ id: 'list_topics', label: 'List Topics', icon: 'list' },
		{ id: 'describe_topic', label: 'Describe Topic', icon: 'info' },
		{ id: 'create_topic', label: 'Create Topic', icon: 'plus' },
		{ id: 'list_consumer_groups', label: 'Consumer Groups', icon: 'users' }
	];
</script>

<div class="bg-surface-800 rounded-lg px-4 py-3">
	<div class="flex items-center gap-2 flex-wrap">
		<span class="text-[10px] font-bold uppercase tracking-wider text-surface-500 mr-2">Quick Actions</span>
		{#each actions as action}
			<button
				type="button"
				class="btn btn-ghost btn-sm"
				{disabled}
				onclick={() => onAction(action.id)}
			>
				{#if action.icon === 'list'}
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
						<path stroke-linecap="round" stroke-linejoin="round" d="M8.25 6.75h12M8.25 12h12m-12 5.25h12M3.75 6.75h.007v.008H3.75V6.75zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zM3.75 12h.007v.008H3.75V12zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm-.375 5.25h.007v.008H3.75v-.008zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z" />
					</svg>
				{:else if action.icon === 'info'}
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
						<path stroke-linecap="round" stroke-linejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
					</svg>
				{:else if action.icon === 'plus'}
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
						<path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
					</svg>
				{:else if action.icon === 'users'}
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
						<path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
					</svg>
				{/if}
				{action.label}
			</button>
		{/each}
	</div>
</div>
