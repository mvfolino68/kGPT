<script lang="ts">
	import type { Snippet } from 'svelte';

	type CardVariant = 'default' | 'subtle' | 'bordered';

	interface Props {
		variant?: CardVariant;
		active?: boolean;
		disabled?: boolean;
		padding?: 'none' | 'sm' | 'md' | 'lg';
		class?: string;
		children: Snippet;
		onclick?: (e: MouseEvent) => void;
	}

	let {
		variant = 'default',
		active = false,
		disabled = false,
		padding = 'md',
		class: className = '',
		children,
		onclick
	}: Props = $props();

	const paddingClasses = {
		none: '',
		sm: 'p-3',
		md: 'p-4',
		lg: 'p-6'
	};

	const variantClasses = {
		default: 'clickable-card',
		subtle: 'clickable-card clickable-card-subtle',
		bordered: 'clickable-card clickable-card-bordered'
	};
</script>

<button
	type="button"
	class="{variantClasses[variant]} {active ? 'clickable-card-active' : ''} {paddingClasses[padding]} {className}"
	{disabled}
	{onclick}
>
	{@render children()}
</button>
