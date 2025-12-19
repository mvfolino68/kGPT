<script lang="ts">
	import Button from './Button.svelte';
	import IconButton from './IconButton.svelte';
	import Icon from './Icon.svelte';

	interface Props {
		onConfirm: () => void;
		onCancel?: () => void;
		itemName?: string;
		size?: 'xs' | 'sm' | 'md';
		class?: string;
	}

	let {
		onConfirm,
		onCancel,
		itemName,
		size = 'sm',
		class: className = ''
	}: Props = $props();

	let confirming = $state(false);

	function handleDeleteClick() {
		confirming = true;
	}

	function handleConfirm() {
		confirming = false;
		onConfirm();
	}

	function handleCancel() {
		confirming = false;
		onCancel?.();
	}

	const buttonSize = $derived(size === 'xs' ? 'sm' : size);
</script>

{#if confirming}
	<div class="flex items-center gap-2 {className}">
		<Button variant="danger" size={buttonSize} onclick={handleConfirm}>
			<Icon name="trash" size="xs" strokeWidth={2} />
			Delete
		</Button>
		<Button variant="ghost" size={buttonSize} onclick={handleCancel}>
			Cancel
		</Button>
	</div>
{:else}
	<IconButton
		variant="danger"
		{size}
		title={itemName ? `Delete ${itemName}` : 'Delete'}
		onclick={handleDeleteClick}
		class={className}
	>
		<Icon name="trash" size="sm" strokeWidth={2} />
	</IconButton>
{/if}
