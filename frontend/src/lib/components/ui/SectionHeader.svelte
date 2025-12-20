<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		as?: 'h3' | 'h4' | 'span' | 'div';
		variant?: 'default' | 'highlight' | 'amber' | 'blue';
		size?: 'xs' | 'sm';
		spacing?: 'none' | 'sm' | 'md';
		class?: string;
		children: Snippet;
		description?: Snippet;
	}

	let {
		as = 'h3',
		variant = 'default',
		size = 'xs',
		spacing = 'md',
		class: className = '',
		children,
		description
	}: Props = $props();

	const variantClasses = {
		default: 'text-surface-500',
		highlight: 'text-emerald-400/80',
		amber: 'text-amber-400',
		blue: 'text-blue-400'
	};

	const sizeClasses = {
		xs: 'text-[10px]',
		sm: 'text-xs'
	};

	const spacingClasses = {
		none: '',
		sm: 'mb-2',
		md: 'mb-3'
	};
</script>

{#if as === 'h3'}
	<h3 class="{sizeClasses[size]} font-bold uppercase tracking-wider {variantClasses[variant]} {spacingClasses[spacing]} {className}">
		{@render children()}
	</h3>
{:else if as === 'h4'}
	<h4 class="{sizeClasses[size]} font-bold uppercase tracking-wider {variantClasses[variant]} {spacingClasses[spacing]} {className}">
		{@render children()}
	</h4>
{:else if as === 'span'}
	<span class="{sizeClasses[size]} font-bold uppercase tracking-wider {variantClasses[variant]} {className}">
		{@render children()}
	</span>
{:else}
	<div class="{sizeClasses[size]} font-bold uppercase tracking-wider {variantClasses[variant]} {spacingClasses[spacing]} {className}">
		{@render children()}
	</div>
{/if}

{#if description}
	<p class="text-xs text-surface-400 mt-1">
		{@render description()}
	</p>
{/if}
