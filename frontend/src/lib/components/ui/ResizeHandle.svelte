<script lang="ts">
	interface Props {
		direction?: 'horizontal' | 'vertical';
		class?: string;
		ariaLabel?: string;
		onmousedown?: (e: MouseEvent) => void;
	}

	let {
		direction = 'horizontal',
		class: className = '',
		ariaLabel = 'Resize',
		onmousedown
	}: Props = $props();

	let resizeHandle: HTMLButtonElement;
</script>

<button
	type="button"
	data-no-hover
	bind:this={resizeHandle}
	{onmousedown}
	class="
		absolute top-0 right-0 w-1 h-full cursor-col-resize
		hover:bg-primary/50 transition-colors group
		{className}
	"
	aria-label={ariaLabel}
>
	<div class="absolute top-1/2 right-0 transform -translate-y-1/2 translate-x-1/2 w-1 h-8 bg-surface-600 group-hover:bg-primary-light rounded-full opacity-0 group-hover:opacity-100 transition-opacity"></div>
</button>
