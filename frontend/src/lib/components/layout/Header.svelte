<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		title: string;
		subtitle?: string;
		actions?: Snippet;
	}

	let { title, subtitle, actions }: Props = $props();
</script>

<header class="h-14 px-6 flex items-center justify-between bg-bg-elevated shadow-[0_1px_0_rgba(255,255,255,0.03)]">
	<div class="flex items-center gap-4">
		<div>
			<h1 class="text-lg font-semibold text-text">{title}</h1>
			{#if subtitle}
				<p class="text-xs text-text-tertiary">{subtitle}</p>
			{/if}
		</div>
	</div>

	{#if actions}
		<div class="flex items-center gap-2">
			{@render actions()}
		</div>
	{/if}
</header>

