<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		padding?: 'none' | 'sm' | 'md' | 'lg';
		class?: string;
		children: Snippet;
	}

	let { padding = 'md', class: className = '', children }: Props = $props();

	const paddingClasses = {
		none: '',
		sm: 'p-2',
		md: 'p-3',
		lg: 'p-4'
	};
</script>

<div class="bg-surface-800/50 rounded-lg border border-surface-700/50 {paddingClasses[padding]} {className}">
	{@render children()}
</div>
