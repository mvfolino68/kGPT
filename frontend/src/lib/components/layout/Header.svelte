<script lang="ts">
	import type { Snippet } from 'svelte';
	import { Button } from '$lib/components/ui';

	interface Props {
		title: string;
		subtitle?: string;
		actions?: Snippet;
	}

	let { title, subtitle, actions }: Props = $props();
</script>

<header class="h-14 px-6 flex items-center justify-between border-b border-surface-700/50 bg-surface-800/30 backdrop-blur-sm">
	<div class="flex items-center gap-4">
		<div>
			<h1 class="text-lg font-semibold text-surface-100">{title}</h1>
			{#if subtitle}
				<p class="text-xs text-surface-500">{subtitle}</p>
			{/if}
		</div>
	</div>

	{#if actions}
		<div class="flex items-center gap-2">
			{@render actions()}
		</div>
	{/if}
</header>
