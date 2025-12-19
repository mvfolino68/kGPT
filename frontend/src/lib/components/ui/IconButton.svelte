<script lang="ts">
	import type { Snippet } from 'svelte';
	import Button from './Button.svelte';

	type IconButtonVariant = 'default' | 'ghost' | 'primary' | 'danger' | 'warning' | 'success';
	type IconButtonSize = 'xs' | 'sm' | 'md';

	interface Props {
		variant?: IconButtonVariant;
		size?: IconButtonSize;
		type?: 'button' | 'submit' | 'reset';
		disabled?: boolean;
		title?: string;
		class?: string;
		children: Snippet;
		onclick?: (e: MouseEvent) => void;
	}

	let {
		variant = 'default',
		size = 'sm',
		type = 'button',
		disabled = false,
		title,
		class: className = '',
		children,
		onclick
	}: Props = $props();

	const buttonSize = $derived(size === 'xs' ? 'icon-sm' : size === 'sm' ? 'icon-md' : 'icon-lg');
	const variantClass = $derived(
		variant === 'default' || variant === 'ghost'
			? 'text-text-secondary hover:text-text hover:bg-surface-hover active:bg-surface-active'
			: variant === 'primary'
				? 'text-primary hover:text-primary-hover hover:bg-primary-bg active:bg-primary/20'
				: variant === 'danger'
					? 'text-error hover:bg-error-bg hover:text-error active:bg-error/20'
					: variant === 'warning'
						? 'text-warning hover:bg-warning-bg active:bg-warning/20'
						: 'text-success hover:bg-success-bg active:bg-success/20'
	);
</script>

<Button
	{type}
	variant="ghost"
	size={buttonSize}
	disabled={disabled}
	title={title}
	onclick={onclick}
	class="rounded-md {variantClass} {className}"
>
	{@render children()}
</Button>
