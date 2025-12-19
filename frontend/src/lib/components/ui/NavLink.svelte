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
		relative flex items-center gap-3 px-3 py-2 rounded-md
		text-sm font-medium
		transition-all duration-150 ease-out
		focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-muted
		no-underline
		{active
			? 'bg-surface-active text-text shadow-sm ring-1 ring-white/10'
			: 'text-text-secondary hover:bg-surface-700 hover:text-text'}
		{className}
	"
>
	{@render children()}
</a>

