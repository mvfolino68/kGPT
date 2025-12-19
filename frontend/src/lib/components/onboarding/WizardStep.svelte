<script lang="ts">
	import { fly } from 'svelte/transition';

	interface Props {
		title: string;
		subtitle?: string;
		children: import('svelte').Snippet;
		actions?: import('svelte').Snippet;
	}

	let { title, subtitle, children, actions }: Props = $props();
</script>

<div
	class="flex flex-col h-full"
	in:fly={{ x: 20, duration: 200, delay: 50 }}
	out:fly={{ x: -20, duration: 150 }}
>
	<div class="text-center mb-8">
		<h2 class="text-2xl font-bold text-surface-100 mb-2">{title}</h2>
		{#if subtitle}
			<p class="text-surface-400 text-sm max-w-md mx-auto">{subtitle}</p>
		{/if}
	</div>

	<div class="flex-1 overflow-y-auto">
		{@render children()}
	</div>

	{#if actions}
		<div class="mt-8 pt-6 border-t border-surface-700/50">
			{@render actions()}
		</div>
	{/if}
</div>
