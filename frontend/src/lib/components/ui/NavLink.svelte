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
	class="
		flex items-center gap-3 px-3 py-2 rounded-md
		text-sm font-medium
		transition-all duration-150 ease-out
		focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-muted
		no-underline
		{active
			? 'bg-surface text-text shadow-sm'
			: 'text-text-secondary hover:bg-surface hover:text-text'}
		{className}
	"
>
	{@render children()}
</a>
