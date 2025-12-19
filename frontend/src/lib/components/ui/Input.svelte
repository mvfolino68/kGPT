<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		type?: 'text' | 'password' | 'email' | 'number' | 'search' | 'url';
		value?: string;
		placeholder?: string;
		disabled?: boolean;
		id?: string;
		name?: string;
		class?: string;
		icon?: Snippet;
		oninput?: (e: Event) => void;
		onkeydown?: (e: KeyboardEvent) => void;
	}

	let {
		type = 'text',
		value = $bindable(''),
		placeholder = '',
		disabled = false,
		id,
		name,
		class: className = '',
		icon,
		oninput,
		onkeydown
	}: Props = $props();
</script>

{#if icon}
	<div class="input-icon-wrapper w-full {className}">
		<span class="input-icon">
			{@render icon()}
		</span>
		<input
			{type}
			{id}
			{name}
			{placeholder}
			{disabled}
			bind:value
			class="input w-full"
			{oninput}
			{onkeydown}
		/>
	</div>
{:else}
	<input
		{type}
		{id}
		{name}
		{placeholder}
		{disabled}
		bind:value
		class="input w-full {className}"
		{oninput}
		{onkeydown}
	/>
{/if}
