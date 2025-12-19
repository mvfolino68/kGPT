<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		href: string;
		active?: boolean;
		class?: string;
		children: Snippet;
	}

	let {
		href,
		active = false,
		class: className = '',
		children
	}: Props = $props();
</script>

<a
	{href}
	aria-current={active ? 'page' : undefined}
	class="
		relative flex items-center gap-3 px-3 py-2 rounded-lg
		text-sm font-medium
		transition-all duration-200 ease-out
		focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:ring-offset-2 focus-visible:ring-offset-bg
		no-underline
		{active
			? 'bg-surface-active text-text shadow-sm ring-1 ring-white/10'
			: 'text-text-secondary hover:bg-surface-hover hover:text-text active:bg-surface-active/60 active:translate-y-px'}
		{className}
	"
>
	{@render children()}
</a>

