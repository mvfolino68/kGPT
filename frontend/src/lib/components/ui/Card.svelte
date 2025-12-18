<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		variant?: 'default' | 'elevated' | 'success' | 'warning' | 'error' | 'primary';
		interactive?: boolean;
		padding?: 'none' | 'sm' | 'md' | 'lg';
		class?: string;
		children: Snippet;
		onclick?: () => void;
	}

	let {
		variant = 'default',
		interactive = false,
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
		default: 'card',
		elevated: 'card card-elevated',
		success: 'card card-success',
		warning: 'card card-warning',
		error: 'card card-error',
		primary: 'card card-primary'
	};
</script>

{#if onclick}
	<button
		type="button"
		class="{variantClasses[variant]} {interactive ? 'card-interactive cursor-pointer' : ''} {paddingClasses[padding]} {className}"
		{onclick}
	>
		{@render children()}
	</button>
{:else}
	<div
		class="{variantClasses[variant]} {interactive ? 'card-interactive' : ''} {paddingClasses[padding]} {className}"
	>
		{@render children()}
	</div>
{/if}
