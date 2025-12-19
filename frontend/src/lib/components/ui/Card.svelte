<script lang="ts">
	import type { Snippet } from 'svelte';

	type CardVariant =
		| 'default'
		| 'elevated'
		| 'interactive'
		| 'glass'
		| 'subtle'
		| 'bordered'
		| 'success'
		| 'warning'
		| 'error';

	interface Props {
		variant?: CardVariant;
		title?: string;
		subtitle?: string;
		header?: Snippet;
		actions?: Snippet;
		padding?: 'none' | 'sm' | 'md' | 'lg';
		footer?: Snippet;
		active?: boolean;
		disabled?: boolean;
		href?: string;
		target?: string;
		rel?: string;
		type?: 'button' | 'submit' | 'reset';
		class?: string;
		children: Snippet;
		onclick?: (e: MouseEvent) => void;
	}

	let {
		variant = 'default',
		title,
		subtitle,
		header,
		actions,
		padding = 'md',
		footer,
		active = false,
		disabled = false,
		href,
		target,
		rel,
		type = 'button',
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

	const hasHeader = $derived(header || title || subtitle || actions);
	const isClickable = $derived(!!href || onclick !== undefined);
	const Tag = $derived(href ? 'a' : isClickable ? 'button' : 'div');

	function handleClick(e: MouseEvent) {
		if (disabled) {
			e.preventDefault();
			e.stopPropagation();
			return;
		}
		onclick?.(e);
	}
</script>

<!--
	Svelte can't statically infer the runtime value of `Tag`. In practice, when clickable we render
	a semantic element (<button> or <a>), so this is safe and accessible.
-->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<svelte:element
	this={Tag}
	class="
		relative rounded-lg overflow-hidden
		shadow-[var(--shadow-card)]
		ring-1 ring-white/[0.075]
		{isClickable ? 'block w-full text-left transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:ring-offset-2 focus-visible:ring-offset-bg disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none' : ''}
		before:content-[''] before:absolute before:inset-0 before:pointer-events-none
		before:bg-gradient-to-b before:from-white/[0.06] before:to-transparent before:opacity-60
		{variant === 'default' ? 'bg-surface-800' : ''}
		{variant === 'elevated' ? 'bg-surface-700 shadow-[var(--shadow-elevated)]' : ''}
		{variant === 'interactive' ? 'bg-surface-800 hover:bg-surface-700 cursor-pointer duration-150 hover:shadow-[var(--shadow-elevated)]' : ''}
		{variant === 'glass' ? 'bg-surface-800/70 supports-[backdrop-filter]:bg-surface-800/60 supports-[backdrop-filter]:backdrop-blur-md ring-white/[0.09]' : ''}
		{variant === 'subtle' ? 'bg-surface-800/80 hover:bg-surface-700/85' : ''}
		{variant === 'bordered' ? 'bg-transparent ring-white/[0.09] hover:bg-surface-900/50' : ''}
		{variant === 'success' ? 'bg-success-bg' : ''}
		{variant === 'warning' ? 'bg-warning-bg' : ''}
		{variant === 'error' ? 'bg-error-bg' : ''}
		{active ? 'bg-surface-hover' : ''}
		{className}
	"
	type={Tag === 'button' ? type : undefined}
	href={Tag === 'a' ? href : undefined}
	target={Tag === 'a' ? target : undefined}
	rel={Tag === 'a' ? rel : undefined}
	disabled={Tag === 'button' ? disabled : undefined}
	aria-disabled={Tag !== 'button' && disabled ? true : undefined}
	tabindex={Tag !== 'button' && disabled ? -1 : undefined}
	onclick={isClickable || disabled ? handleClick : undefined}
>
	{#if hasHeader}
		{#if header}
			<div class="relative px-4 py-3 border-b border-white/5">
				{@render header()}
			</div>
		{:else}
			<div class="relative px-4 py-3 flex items-center justify-between gap-4 {title || subtitle ? 'border-b border-white/5' : ''}">
				<div class="flex-1 min-w-0">
					{#if title}
						<h3 class="text-sm font-medium text-text">{title}</h3>
					{/if}
					{#if subtitle}
						<p class="text-xs text-text-tertiary mt-0.5">{subtitle}</p>
					{/if}
				</div>
				{#if actions}
					<div class="flex items-center gap-2 shrink-0">
						{@render actions()}
					</div>
				{/if}
			</div>
		{/if}
	{/if}
	<div class="relative {paddingClasses[padding]}">
		{@render children()}
	</div>
	{#if footer}
		<div class="relative px-4 py-3 flex justify-end border-t border-white/5">
			{@render footer()}
		</div>
	{/if}
</svelte:element>
