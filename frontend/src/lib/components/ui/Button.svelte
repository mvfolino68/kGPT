<script lang="ts">
	import type { Snippet } from 'svelte';

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

	interface Props {
		variant?: ButtonVariant;
		size?: ButtonSize;
		type?: 'button' | 'submit' | 'reset';
		disabled?: boolean;
		loading?: boolean;
		title?: string;
		ariaLabel?: string;
		class?: string;
		children: Snippet;
		onclick?: (e: MouseEvent) => void;
	}

	let {
		variant = 'secondary',
		size = 'md',
		type = 'button',
		disabled = false,
		loading = false,
		title,
		ariaLabel,
		class: className = '',
		children,
		onclick
	}: Props = $props();

	const isIconSize = $derived(size.startsWith('icon-'));
</script>

<button
	{type}
	class="
		inline-flex items-center justify-center gap-1.5
		font-medium rounded-md
		transition-all duration-150 ease-out
		focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:ring-offset-2 focus-visible:ring-offset-bg
		disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none
		{variant === 'default' ? 'bg-surface-hover text-text-secondary hover:bg-surface-active hover:text-text' : ''}
		{variant === 'primary' ? 'bg-primary text-black hover:bg-primary-hover active:scale-[0.98]' : ''}
		{variant === 'secondary' ? 'bg-surface-hover text-text-secondary hover:bg-surface-active hover:text-text' : ''}
		{variant === 'ghost' ? 'bg-transparent text-text-secondary hover:bg-surface-hover hover:text-text' : ''}
		{variant === 'danger' ? 'bg-error/10 text-error hover:bg-error/20' : ''}
		{variant === 'danger-solid' ? 'bg-error text-white hover:bg-error/90 active:scale-[0.98]' : ''}
		{variant === 'success' ? 'bg-success/10 text-success hover:bg-success/20' : ''}
		{variant === 'warning' ? 'bg-warning/10 text-warning hover:bg-warning/20' : ''}
		{variant === 'link' ? 'bg-transparent text-primary hover:text-primary-hover underline-offset-2 hover:underline px-0' : ''}
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
	disabled={disabled || loading}
	{title}
	aria-label={ariaLabel}
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
