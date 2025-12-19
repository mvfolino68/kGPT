<script lang="ts">
	import type { Snippet } from 'svelte';
	import { fade, fly } from 'svelte/transition';

	type Position = 'top' | 'bottom' | 'left' | 'right';

	interface Props {
		text: string;
		position?: Position;
		class?: string;
		delay?: number;
		children: Snippet;
	}

	let {
		text,
		position = 'top',
		class: className = '',
		delay = 100, // Short delay by default to prevent accidental flashes
		children
	}: Props = $props();

	let visible = $state(false);
	let timeoutId: ReturnType<typeof setTimeout>;

	function show() {
		if (timeoutId) clearTimeout(timeoutId);
		timeoutId = setTimeout(() => {
			visible = true;
		}, delay);
	}

	function hide() {
		if (timeoutId) clearTimeout(timeoutId);
		visible = false;
	}

	const positionClasses: Record<Position, string> = {
		top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
		bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
		left: 'right-full top-1/2 -translate-y-1/2 mr-2',
		right: 'left-full top-1/2 -translate-y-1/2 ml-2'
	};

	const arrowPosition: Record<Position, string> = {
		top: 'top-full left-1/2 -translate-x-1/2 -mt-1 border-b border-r',
		bottom: 'bottom-full left-1/2 -translate-x-1/2 -mb-1 border-t border-l',
		left: 'left-full top-1/2 -translate-y-1/2 -ml-1 border-t border-r',
		right: 'right-full top-1/2 -translate-y-1/2 -mr-1 border-b border-l'
	};

	function getTransitionParams(pos: Position) {
		switch (pos) {
			case 'top': return { y: 5, duration: 200 };
			case 'bottom': return { y: -5, duration: 200 };
			case 'left': return { x: 5, duration: 200 };
			case 'right': return { x: -5, duration: 200 };
		}
	}
</script>

<div
	class="relative inline-flex {className}"
	role="presentation"
	onmouseenter={show}
	onmouseleave={hide}
	onfocus={show}
	onblur={hide}
>
	{@render children()}

	{#if visible && text}
		<div
			class="absolute z-50 {positionClasses[position]} pointer-events-none filter drop-shadow-lg"
			role="tooltip"
			in:fly={getTransitionParams(position)}
			out:fade={{ duration: 150 }}
		>
			<div class="bg-bg-elevated border border-border-subtle text-text text-xs px-3 py-2 rounded-md whitespace-nowrap relative">
				{text}
				<div class="absolute w-2 h-2 bg-bg-elevated border-border-subtle rotate-45 {arrowPosition[position]}"></div>
			</div>
		</div>
	{/if}
</div>
