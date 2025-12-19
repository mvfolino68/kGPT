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
	class="nav-link {active ? 'nav-link-active' : ''} {className}"
>
	{@render children()}
</a>
