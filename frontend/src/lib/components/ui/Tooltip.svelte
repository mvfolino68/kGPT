<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		text: string;
		position?: 'top' | 'bottom' | 'left' | 'right';
		class?: string;
		children: Snippet;
	}

	let {
		text,
		position = 'top',
		class: className = '',
		children
	}: Props = $props();

	let visible = $state(false);

	const positionClasses = {
		top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
		bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
		left: 'right-full top-1/2 -translate-y-1/2 mr-2',
		right: 'left-full top-1/2 -translate-y-1/2 ml-2'
	};

	const arrowClasses = {
		top: 'top-full left-1/2 -translate-x-1/2 border-t-surface-700 border-x-transparent border-b-transparent',
		bottom: 'bottom-full left-1/2 -translate-x-1/2 border-b-surface-700 border-x-transparent border-t-transparent',
		left: 'left-full top-1/2 -translate-y-1/2 border-l-surface-700 border-y-transparent border-r-transparent',
		right: 'right-full top-1/2 -translate-y-1/2 border-r-surface-700 border-y-transparent border-l-transparent'
	};
</script>

<div
	class="relative inline-flex {className}"
	onmouseenter={() => visible = true}
	onmouseleave={() => visible = false}
	onfocus={() => visible = true}
	onblur={() => visible = false}
>
	{@render children()}

	{#if visible && text}
		<div
			class="absolute z-50 {positionClasses[position]} pointer-events-none animate-fade-in"
			role="tooltip"
		>
			<div class="bg-surface-700 text-surface-100 text-xs px-2 py-1 rounded shadow-lg whitespace-nowrap">
				{text}
			</div>
			<div class="absolute w-0 h-0 border-4 {arrowClasses[position]}"></div>
		</div>
	{/if}
</div>
