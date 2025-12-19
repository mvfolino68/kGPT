<script lang="ts">
	import type { Snippet } from 'svelte';

	type IconButtonVariant = 'default' | 'primary' | 'danger' | 'warning' | 'success';
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

	const variantClasses: Record<IconButtonVariant, string> = {
		default: 'btn-action btn-action-default',
		primary: 'btn-action btn-action-primary',
		danger: 'btn-action btn-action-danger',
		warning: 'btn-action btn-action-warning',
		success: 'btn-action btn-action-success'
	};

	const sizeClasses: Record<IconButtonSize, string> = {
		xs: 'p-1',
		sm: 'p-1.5',
		md: 'p-2'
	};

	const iconSizes: Record<IconButtonSize, string> = {
		xs: '[&>svg]:w-3 [&>svg]:h-3',
		sm: '[&>svg]:w-4 [&>svg]:h-4',
		md: '[&>svg]:w-5 [&>svg]:h-5'
	};
</script>

<button
	{type}
	class="{variantClasses[variant]} {sizeClasses[size]} {iconSizes[size]} {className}"
	{disabled}
	{title}
	{onclick}
>
	{@render children()}
</button>
