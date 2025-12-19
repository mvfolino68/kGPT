<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		label: string;
		id?: string;
		hint?: string;
		error?: string;
		children: Snippet;
	}

	let {
		label,
		id,
		hint,
		error,
		children
	}: Props = $props();
</script>

<div class="space-y-1.5">
	<label for={id} class="label block">
		{label}
	</label>
	{@render children()}
	{#if error}
		<p class="text-xs text-error">{error}</p>
	{:else if hint}
		<p class="text-xs text-text-tertiary">{hint}</p>
	{/if}
</div>
