<script lang="ts">
	import type { Snippet } from 'svelte';
	import type { HTMLButtonAttributes } from 'svelte/elements';

	// Note: we keep a few legacy variant/size names for backwards compatibility
	// while the canonical design system stays centered on primary/secondary/ghost/etc.
	type ButtonVariant =
		| 'primary'
		| 'secondary'
		| 'ghost'
		| 'danger'
		| 'danger-solid'
		| 'success'
		| 'warning'
		| 'link'
		| 'default';

	type ButtonSize = 'xs' | 'sm' | 'md' | 'lg' | 'icon' | 'icon-sm' | 'icon-md' | 'icon-lg';

	interface Props extends HTMLButtonAttributes {
		variant?: ButtonVariant;
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
</script>

<button
	{type}
	class="
		inline-flex items-center justify-center gap-1.5
		font-medium rounded-md
		transition-all duration-150 ease-out
		focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:ring-offset-2 focus-visible:ring-offset-bg
		disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none
		{variant === 'default' ? 'bg-surface text-text-secondary hover:bg-surface-700 hover:text-text active:bg-surface-active active:translate-y-px' : ''}
		{variant === 'primary' ? 'bg-primary-bg text-primary border border-primary/30 hover:bg-primary-bg/80 hover:border-primary/50 active:translate-y-px active:scale-[0.99]' : ''}
		{variant === 'secondary' ? 'bg-surface text-text-secondary hover:bg-surface-700 hover:text-text active:bg-surface-active active:translate-y-px' : ''}
		{variant === 'ghost' ? 'bg-transparent text-text-secondary hover:bg-surface-700 hover:text-text active:bg-surface-active/60 active:translate-y-px' : ''}
		{variant === 'danger' ? 'bg-error/10 text-error hover:bg-error/20 active:translate-y-px' : ''}
		{variant === 'danger-solid' ? 'bg-error text-white hover:bg-error/90 active:translate-y-px active:scale-[0.99]' : ''}
		{variant === 'success' ? 'bg-success/10 text-success hover:bg-success/20 active:translate-y-px' : ''}
		{variant === 'warning' ? 'bg-warning/10 text-warning hover:bg-warning/20 active:translate-y-px' : ''}
		{variant === 'link' ? 'bg-transparent text-primary hover:text-primary-hover hover:bg-primary-bg/30 active:bg-primary-bg/50 px-0' : ''}
		{size === 'xs' ? 'px-2 py-1 text-xs' : ''}
		{size === 'sm' ? 'px-2.5 py-1 text-xs' : ''}
		{size === 'md' ? 'px-3 py-1.5 text-sm' : ''}
		{size === 'lg' ? 'px-4 py-2 text-sm' : ''}
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
