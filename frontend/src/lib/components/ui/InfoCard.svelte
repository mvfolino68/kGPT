<script lang="ts">
	import type { Snippet } from 'svelte';
	import SectionHeader from './SectionHeader.svelte';
	import InnerCard from './InnerCard.svelte';

	interface Props {
		title: string;
		variant?: 'default' | 'highlight' | 'amber' | 'blue';
		padding?: 'sm' | 'md' | 'lg';
		class?: string;
		children: Snippet;
		actions?: Snippet;
	}

	let {
		title,
		variant = 'default',
		padding = 'lg',
		class: className = '',
		children,
		actions
	}: Props = $props();
</script>

<InnerCard {padding} class={className}>
	<div class="flex items-center justify-between mb-3">
		<SectionHeader {variant} spacing="none">{title}</SectionHeader>
		{#if actions}
			{@render actions()}
		{/if}
	</div>
	{@render children()}
</InnerCard>
