<script lang="ts">
	import type { Snippet } from 'svelte';
	import Button from './Button.svelte';

	type CardButtonVariant = 'default' | 'active' | 'selected';
	type CardButtonSize = 'sm' | 'md' | 'lg';

	interface Props {
		variant?: CardButtonVariant;
		size?: CardButtonSize;
		type?: 'button' | 'submit' | 'reset';
		disabled?: boolean;
		selected?: boolean;
		active?: boolean;
		class?: string;
		children: Snippet;
		onclick?: (e: MouseEvent) => void;
	}

	let {
		variant = 'default',
		size = 'md',
		type = 'button',
		disabled = false,
		selected = false,
		active = false,
		class: className = '',
		children,
		onclick
	}: Props = $props();

	const sizeClasses = $derived(
		size === 'sm' ? 'p-2.5' : size === 'md' ? 'p-3' : 'p-4'
	);

	const variantClasses = $derived(
		variant === 'active' || active
			? 'bg-surface-active border-surface-600 shadow-lg hover:bg-surface-active/90 hover:border-surface-500 hover:shadow-xl'
			: variant === 'selected' || selected
				? 'bg-bg-elevated border-white/5 ring-1 ring-white/10 hover:bg-surface-800/50 hover:border-white/10'
				: 'bg-bg-elevated border-white/5 hover:bg-surface-800/50 hover:border-white/10'
	);
</script>

<Button
	{type}
	{disabled}
	{onclick}
	variant="secondary"
	class="
		text-left justify-start h-auto w-full rounded-xl border
		transition-all duration-150 ease-out
		{sizeClasses}
		{variantClasses}
		{selected ? 'ring-1 ring-white/10' : ''}
		{active ? 'shadow-lg' : ''}
		{className}
	"
>
	{@render children()}
</Button>
