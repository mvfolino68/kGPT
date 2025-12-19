<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	type TabItem = {
		id: string;
		label: string;
		icon?: string;
	};

	let { items, active } = $props<{
		items: TabItem[];
		active: string;
	}>();

	const dispatch = createEventDispatcher<{
		change: string;
	}>();

	function handleKeydown(e: KeyboardEvent, id: string) {
		if (e.key === 'Enter' || e.key === ' ') {
			dispatch('change', id);
		}
	}
</script>

<div class="flex gap-1" role="tablist" aria-orientation="horizontal">
	{#each items as item}
		{@const isActive = active === item.id}
		<button
			type="button"
			role="tab"
			aria-selected={isActive}
			tabindex={isActive ? 0 : -1}
			class="
				relative px-4 py-3 text-sm font-medium transition-all duration-200 outline-none rounded-t-lg
				{isActive ? 'text-primary' : 'text-text-secondary hover:text-text'}
			"
			onclick={() => dispatch('change', item.id)}
			onkeydown={(e) => handleKeydown(e, item.id)}
		>
			<span class="relative z-10 flex items-center gap-2">
				{#if item.icon}
					<i class="icon-{item.icon}" /> <!-- Placeholder for icon if needed -->
				{/if}
				{item.label}
			</span>

			{#if isActive}
				<div
					class="absolute bottom-0 left-0 right-0 h-0.5 bg-primary shadow-[0_-2px_8px_rgba(56,125,255,0.4)]"
					style="view-transition-name: active-tab-indicator"
				/>
			{/if}

			{#if !isActive}
				<!-- Hover effect -->
				<div class="absolute inset-0 bg-surface-hover opacity-0 hover:opacity-100 rounded-lg transition-opacity duration-200 -z-0 scale-90" />
			{/if}
		</button>
	{/each}
</div>
