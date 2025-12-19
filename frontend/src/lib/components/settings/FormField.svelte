<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		label: string;
		id?: string;
		hint?: string;
		children: Snippet;
	}

	let {
		label,
		id,
		hint,
		children
	}: Props = $props();
</script>

<div class="space-y-1.5">
	<label for={id} class="block text-[11px] font-medium uppercase tracking-wider text-surface-500">
		{label}
	</label>
	{@render children()}
	{#if hint}
		<p class="text-xs text-surface-500">{hint}</p>
	{/if}
</div>
