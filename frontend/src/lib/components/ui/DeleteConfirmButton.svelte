<script lang="ts">
	import { Button, Icon } from '$lib/components/ui';

	interface Props {
		itemId: number | string;
		title?: string;
		onConfirm: (id: any) => void;
		size?: 'xs' | 'sm' | 'md';
		iconSize?: 'xs' | 'sm';
		className?: string;
	}

	let {
		itemId,
		title = 'Delete item',
		onConfirm,
		size = 'sm',
		iconSize = 'xs',
		className = ''
	}: Props = $props();

	let confirming = $state(false);

	function handleClick() {
		if (confirming) {
			onConfirm(itemId);
			confirming = false;
		} else {
			confirming = true;
			// Reset after 3 seconds
			setTimeout(() => {
				confirming = false;
			}, 3000);
		}
	}
</script>

{#if confirming}
	<Button
		variant="danger"
		{size}
		class="px-2 text-xs {className}"
		onclick={handleClick}
		title="Confirm delete"
	>
		Confirm
	</Button>
{:else}
	<Button
		variant="ghost"
		size="icon-{size}"
		class="text-surface-500 hover:text-red-400 hover:bg-red-400/10 {className}"
		onclick={handleClick}
		{title}
	>
		<Icon name="trash" size={iconSize} />
	</Button>
{/if}
