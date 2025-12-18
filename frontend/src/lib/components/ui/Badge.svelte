<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		variant?: 'default' | 'primary' | 'success' | 'warning' | 'error';
		size?: 'sm' | 'md';
		class?: string;
		children: Snippet;
	}

	let {
		variant = 'default',
		size = 'md',
		class: className = '',
		children
	}: Props = $props();

	const variantClasses = {
		default: 'badge badge-default',
		primary: 'badge badge-primary',
		success: 'badge badge-success',
		warning: 'badge badge-warning',
		error: 'badge badge-error'
	};

	const sizeClasses = {
		sm: 'text-xs px-1.5 py-0.5',
		md: ''
	};
</script>

<span class="{variantClasses[variant]} {sizeClasses[size]} {className}">
	{@render children()}
</span>
