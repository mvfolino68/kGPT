<script lang="ts">
	import type { Snippet } from 'svelte';

	type ListItemVariant = 'default' | 'subtle';

	interface Props {
		variant?: ListItemVariant;
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
	class="list-item {variant === 'subtle' ? 'list-item-subtle' : ''} {active ? 'list-item-active' : ''} {className}"
	{disabled}
	{onclick}
>
	{@render children()}
</button>
