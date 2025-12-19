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
		error?: boolean;
		oninput?: (e: Event) => void;
		onkeydown?: (e: KeyboardEvent) => void;
		onfocus?: (e: FocusEvent) => void;
		onblur?: (e: FocusEvent) => void;
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
		error = false,
		oninput,
		onkeydown,
		onfocus,
		onblur
	}: Props = $props();
</script>

{#if icon}
	<div class="relative w-full {className}">
		<span class="absolute left-3 top-1/2 -translate-y-1/2 text-text-tertiary w-4 h-4 pointer-events-none">
			{@render icon()}
		</span>
		<input
			{type}
			{id}
			{name}
			{placeholder}
			{disabled}
			bind:value
			class="
				w-full bg-surface-hover rounded-md px-3 py-2 text-sm text-text pl-10
				placeholder:text-text-tertiary
				transition-colors duration-150
				focus:outline-none focus:bg-surface-active focus:ring-1 focus:ring-primary/50
				disabled:opacity-50 disabled:cursor-not-allowed
				{error ? 'ring-1 ring-error/50' : ''}
			"
			{oninput}
			{onkeydown}
			{onfocus}
			{onblur}
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
		class="
			w-full bg-surface-hover rounded-md px-3 py-2 text-sm text-text
			placeholder:text-text-tertiary
			transition-colors duration-150
			focus:outline-none focus:bg-surface-active focus:ring-1 focus:ring-primary/50
			disabled:opacity-50 disabled:cursor-not-allowed
			{error ? 'ring-1 ring-error/50' : ''}
			{className}
		"
		{oninput}
		{onkeydown}
		{onfocus}
		{onblur}
	/>
{/if}
