<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		variant?: 'default' | 'subtle';
		active?: boolean;
		disabled?: boolean;
		class?: string;
		children: Snippet;
		onclick?: (e: MouseEvent) => void;
	}

	let {
		variant = 'default',
		active = false,
		disabled = false,
		class: className = '',
		children,
		onclick
	}: Props = $props();
</script>

<button
	type="button"
	class="
		w-full text-left px-4 py-2.5 rounded-md
		transition-colors duration-150
		focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-primary/50
		disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none
		{active
			? 'bg-surface-hover text-text'
			: variant === 'subtle'
				? 'text-text-secondary hover:bg-surface-hover/60 hover:text-text'
				: 'text-text-secondary hover:bg-surface hover:text-text'}
		{className}
	"
	{disabled}
	{onclick}
>
	{@render children()}
</button>
