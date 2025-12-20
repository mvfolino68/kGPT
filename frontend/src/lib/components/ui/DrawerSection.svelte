<script lang="ts">
	import type { Snippet } from 'svelte';
	import SectionHeader from './SectionHeader.svelte';

	interface Props {
		title: string;
		variant?: 'default' | 'highlight' | 'amber' | 'blue';
		border?: boolean;
		class?: string;
		children: Snippet;
	}

	let {
		title,
		variant = 'default',
		border = true,
		class: className = '',
		children
	}: Props = $props();
</script>

<section class="p-4 {border ? 'border-b border-surface-700/50' : ''} {className}">
	<SectionHeader {variant} spacing="sm">{title}</SectionHeader>
	{@render children()}
</section>
