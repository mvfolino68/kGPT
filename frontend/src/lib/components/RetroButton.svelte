<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		variant?: 'default' | 'primary' | 'danger' | 'ghost' | 'confluent';
		size?: 'sm' | 'md' | 'lg';
		disabled?: boolean;
		type?: 'button' | 'submit' | 'reset';
		class?: string;
		onclick?: (e: MouseEvent) => void;
		children: Snippet;
	}

	let {
		variant = 'default',
		size = 'md',
		disabled = false,
		type = 'button',
		class: className = '',
		onclick,
		children
	}: Props = $props();

	const sizeClasses = {
		sm: 'px-2.5 py-1 text-xs',
		md: 'px-4 py-2 text-sm',
		lg: 'px-6 py-2.5 text-base'
	};

	const variantClasses = {
		default: 'retro-button',
		primary: 'retro-button retro-button-primary',
		danger: 'retro-button retro-button-danger',
		ghost: 'bg-transparent border-transparent hover:bg-surface-800/50 hover:border-white/10',
		confluent: 'retro-button retro-button-confluent'
	};
</script>

<button
	{type}
	{disabled}
	{onclick}
	class="{variantClasses[variant]} {sizeClasses[size]} rounded font-mono {className}"
>
	{@render children()}
</button>

