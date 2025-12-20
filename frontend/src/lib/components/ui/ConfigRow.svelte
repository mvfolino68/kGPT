<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		label: string;
		value?: string | number | null;
		variant?: 'default' | 'success' | 'warning' | 'muted';
		class?: string;
		children?: Snippet;
	}

	let { label, value, variant = 'default', class: className = '', children }: Props = $props();

	const variantClasses = {
		default: 'text-surface-300',
		success: 'text-emerald-400/80',
		warning: 'text-amber-400/80',
		muted: 'text-surface-500'
	};
</script>

<div class="flex justify-between text-sm {className}">
	<dt class="text-surface-500">{label}</dt>
	{#if children}
		<dd>{@render children()}</dd>
	{:else}
		<dd class={variantClasses[variant]}>{value ?? '—'}</dd>
	{/if}
</div>
