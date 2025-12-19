<script lang="ts">
	interface Option {
		value: string;
		label: string;
	}

	interface Props {
		value?: string;
		options: Option[] | string[];
		placeholder?: string;
		disabled?: boolean;
		id?: string;
		name?: string;
		class?: string;
		error?: boolean;
		onchange?: (e: Event) => void;
	}

	let {
		value = $bindable(''),
		options,
		placeholder,
		disabled = false,
		id,
		name,
		class: className = '',
		error = false,
		onchange
	}: Props = $props();

	// Normalize options to always be { value, label } format
	const normalizedOptions = $derived(
		options.map((opt) =>
			typeof opt === 'string' ? { value: opt, label: opt } : opt
		)
	);
</script>

<div class="relative {className}">
	<select
		{id}
		{name}
		{disabled}
		bind:value
		class="
			w-full bg-surface-hover rounded-md px-3 py-2 text-sm text-text
			transition-colors duration-150
			focus:outline-none focus:bg-surface-active focus:ring-1 focus:ring-primary/50
			disabled:opacity-50 disabled:cursor-not-allowed
			appearance-none cursor-pointer pr-10
			{error ? 'ring-1 ring-error/50' : ''}
		"
		{onchange}
	>
		{#if placeholder}
			<option value="" disabled>{placeholder}</option>
		{/if}
		{#each normalizedOptions as option}
			<option value={option.value}>{option.label}</option>
		{/each}
	</select>
	<svg
		class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-tertiary pointer-events-none"
		fill="none"
		stroke="currentColor"
		viewBox="0 0 24 24"
		stroke-width="2"
	>
		<path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
	</svg>
</div>
