<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		variant?: 'default' | 'primary' | 'ghost' | 'danger';
		size?: 'sm' | 'md' | 'lg' | 'icon';
		type?: 'button' | 'submit' | 'reset';
		disabled?: boolean;
		loading?: boolean;
		class?: string;
		children: Snippet;
		onclick?: (e: MouseEvent) => void;
	}

	let {
		variant = 'default',
		size = 'md',
		type = 'button',
		disabled = false,
		loading = false,
		class: className = '',
		children,
		onclick
	}: Props = $props();

	const variantClasses = {
		default: 'btn btn-default',
		primary: 'btn btn-primary',
		ghost: 'btn btn-ghost',
		danger: 'btn btn-danger'
	};

	const sizeClasses = {
		sm: 'btn-sm',
		md: '',
		lg: 'btn-lg',
		icon: 'btn-icon'
	};
</script>

<button
	{type}
	class="{variantClasses[variant]} {sizeClasses[size]} {className}"
	disabled={disabled || loading}
	{onclick}
>
	{#if loading}
		<svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
			<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
			<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
		</svg>
	{/if}
	{@render children()}
</button>
