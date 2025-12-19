<script lang="ts">
	import type { Snippet } from 'svelte';

	type BadgeVariant = 'default' | 'primary' | 'success' | 'warning' | 'error' | 'info';
	type BadgeSize = 'sm' | 'md';

	interface Props {
		variant?: BadgeVariant;
		size?: BadgeSize;
		class?: string;
		children: Snippet;
	}

	let {
		variant = 'default',
		size = 'md',
		class: className = '',
		children
	}: Props = $props();
</script>

<span
	class="
		inline-flex items-center gap-1 rounded-full font-medium
		{variant === 'default' ? 'bg-surface-hover text-text-secondary' : ''}
		{variant === 'primary' ? 'bg-primary/15 text-primary' : ''}
		{variant === 'success' ? 'bg-success/15 text-success' : ''}
		{variant === 'warning' ? 'bg-warning/15 text-warning' : ''}
		{variant === 'error' ? 'bg-error/15 text-error' : ''}
		{variant === 'info' ? 'bg-info/15 text-info' : ''}
		{size === 'sm' ? 'text-[10px] px-1.5 py-0.5' : ''}
		{size === 'md' ? 'text-xs px-2 py-0.5' : ''}
		{className}
	"
>
	{@render children()}
</span>
