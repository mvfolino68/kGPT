<script lang="ts">
	interface Props {
		value?: string;
		placeholder?: string;
		disabled?: boolean;
		id?: string;
		name?: string;
		rows?: number;
		class?: string;
		error?: boolean;
		autoResize?: boolean;
		oninput?: (e: Event) => void;
		onkeydown?: (e: KeyboardEvent) => void;
		onfocus?: (e: FocusEvent) => void;
		onblur?: (e: FocusEvent) => void;
	}

	let {
		value = $bindable(''),
		placeholder = '',
		disabled = false,
		id,
		name,
		rows = 3,
		class: className = '',
		error = false,
		autoResize = false,
		oninput,
		onkeydown,
		onfocus,
		onblur
	}: Props = $props();

	const textareaClasses = `
		w-full bg-surface-800 rounded-md px-3 py-2 text-sm text-text
		border border-surface-700
		placeholder:text-text-tertiary
		transition-colors duration-150
		focus:outline-none focus:bg-surface-700 focus:ring-1 focus:ring-primary/50 focus:border-primary/50
		disabled:opacity-50 disabled:cursor-not-allowed
		resize-none
	`.trim().replace(/\s+/g, ' ');

	const errorClasses = $derived(error ? 'border-error focus:border-error' : '');
	const autoResizeStyle = $derived(autoResize ? 'field-sizing: content; max-height: 200px;' : '');
</script>

<textarea
	{id}
	{name}
	{placeholder}
	{disabled}
	{rows}
	bind:value
	class="{textareaClasses} {errorClasses} {className}"
	style={autoResizeStyle}
	{oninput}
	{onkeydown}
	{onfocus}
	{onblur}
></textarea>
