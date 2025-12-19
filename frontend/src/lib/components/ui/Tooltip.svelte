<script lang="ts">
	import type { Snippet } from 'svelte';

	type Position = 'top' | 'bottom' | 'left' | 'right';

	interface Props {
		text: string;
		position?: Position;
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

	const positionClasses: Record<Position, string> = {
		top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
		bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
		left: 'right-full top-1/2 -translate-y-1/2 mr-2',
		right: 'left-full top-1/2 -translate-y-1/2 ml-2'
	};

	const arrowPosition: Record<Position, string> = {
		top: 'top-full left-1/2 -translate-x-1/2 -mt-1',
		bottom: 'bottom-full left-1/2 -translate-x-1/2 -mb-1',
		left: 'left-full top-1/2 -translate-y-1/2 -ml-1',
		right: 'right-full top-1/2 -translate-y-1/2 -mr-1'
	};
</script>

<div
	class="relative inline-flex {className}"
	role="presentation"
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
			<div class="bg-surface-active text-text text-xs px-2.5 py-1.5 rounded-md shadow-lg whitespace-nowrap">
				{text}
			</div>
			<div class="absolute w-2 h-2 bg-surface-active rotate-45 {arrowPosition[position]}"></div>
		</div>
	{/if}
</div>
