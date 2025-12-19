<script lang="ts">
	import type { Snippet } from 'svelte';
	import type { HTMLButtonAttributes } from 'svelte/elements';

	type ButtonVariant =
		| 'primary'
		| 'secondary'
		| 'ghost'
		| 'danger'
		| 'danger-solid'
		| 'success'
		| 'warning'
		| 'link';

	type ButtonSize = 'xs' | 'sm' | 'md' | 'lg' | 'icon' | 'icon-sm' | 'icon-md' | 'icon-lg';

	interface Props extends HTMLButtonAttributes {
		variant?: ButtonVariant | 'default'; // keep 'default' in props for compat, map to secondary
		size?: ButtonSize;
		loading?: boolean;
		title?: string;
		// Backwards compatible alias for `aria-label`
		ariaLabel?: string;
		children: Snippet;
	}

	let {
		variant = 'secondary',
		size = 'md',
		type = 'button',
		disabled: disabledProp = false,
		loading = false,
		title,
		ariaLabel,
		'aria-label': ariaLabelAttr,
		class: className = '',
		children,
		onclick
	}: Props = $props();

	const isIconSize = $derived(size.startsWith('icon-'));
	const resolvedAriaLabel = $derived(ariaLabel ?? ariaLabelAttr);

	// Map 'default' to 'secondary' logic
	const activeVariant = $derived(variant === 'default' ? 'secondary' : variant);
</script>

<button
	{type}
	data-no-hover="true"
	class="
		inline-flex items-center justify-center gap-2
		font-medium rounded-lg
		transition-all duration-200 ease-out
		focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:ring-offset-2 focus-visible:ring-offset-bg
		disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none
		{activeVariant === 'primary' ? 'bg-primary-bg text-primary border border-primary/20 hover:bg-primary-bg/80 hover:border-primary/40 active:translate-y-px active:scale-[0.99]' : ''}
		{activeVariant === 'secondary' ? 'bg-surface text-text-secondary border border-surface-hover hover:bg-surface-hover hover:text-text hover:border-surface-active active:bg-surface-active active:translate-y-px' : ''}
		{activeVariant === 'ghost' ? 'bg-transparent text-text-secondary hover:bg-surface-hover hover:text-text active:bg-surface-active/60 active:translate-y-px' : ''}
		{activeVariant === 'danger' ? 'bg-error-bg text-error border border-error/20 hover:bg-error-bg/80 hover:border-error/40 active:translate-y-px' : ''}
		{activeVariant === 'danger-solid' ? 'bg-error text-white hover:bg-error/90 shadow-md shadow-error/20 active:translate-y-px active:scale-[0.99]' : ''}
		{activeVariant === 'success' ? 'bg-success-bg text-success border border-success/20 hover:bg-success-bg/80 hover:border-success/40 active:translate-y-px' : ''}
		{activeVariant === 'warning' ? 'bg-warning-bg text-warning border border-warning/20 hover:bg-warning-bg/80 hover:border-warning/40 active:translate-y-px' : ''}
		{activeVariant === 'link' ? 'bg-transparent text-primary hover:text-primary-hover hover:underline underline-offset-4 decoration-primary/30 px-0 h-auto' : ''}
		{size === 'xs' ? 'px-2.5 py-1 text-xs' : ''}
		{size === 'sm' ? 'px-3 py-1.5 text-xs' : ''}
		{size === 'md' ? 'px-4 py-2 text-sm' : ''}
		{size === 'lg' ? 'px-5 py-2.5 text-base' : ''}
		{size === 'icon' ? 'p-2 [&>svg]:w-4 [&>svg]:h-4' : ''}
		{size === 'icon-sm' ? 'p-1.5 [&>svg]:w-3.5 [&>svg]:h-3.5' : ''}
		{size === 'icon-md' ? 'p-2 [&>svg]:w-4 [&>svg]:h-4' : ''}
		{size === 'icon-lg' ? 'p-2.5 [&>svg]:w-5 [&>svg]:h-5' : ''}
		{className}
	"
	disabled={disabledProp || loading}
	{title}
	aria-label={resolvedAriaLabel}
	{onclick}
>
	{#if loading}
		<svg class="animate-spin {isIconSize ? '' : 'w-3.5 h-3.5'}" fill="none" viewBox="0 0 24 24">
			<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
			<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
		</svg>
	{/if}
	{#if !loading || !isIconSize}
		{@render children()}
	{/if}
</button>
