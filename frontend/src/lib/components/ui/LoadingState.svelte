<script lang="ts">
	import Icon from './Icon.svelte';

	interface Props {
		message?: string;
		showSpinner?: boolean;
		size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
		class?: string;
	}

	let {
		message = 'Loading...',
		showSpinner = true,
		size = 'sm',
		class: className = ''
	}: Props = $props();

	const textSizeClasses: Record<'xs' | 'sm' | 'md' | 'lg' | 'xl', string> = {
		xs: 'text-xs',
		sm: 'text-sm',
		md: 'text-base',
		lg: 'text-lg',
		xl: 'text-xl'
	};

	const spinnerSizeClasses: Record<'xs' | 'sm' | 'md' | 'lg' | 'xl', 'xs' | 'sm' | 'md' | 'lg' | 'xl'> = {
		xs: 'xs',
		sm: 'sm',
		md: 'md',
		lg: 'lg',
		xl: 'xl'
	};
</script>

<div class="flex items-center gap-2 {textSizeClasses[size]} text-surface-500 {className}">
	{#if showSpinner}
		<Icon name="spinner" size={spinnerSizeClasses[size]} class="animate-spin text-text-tertiary" />
	{/if}
	<span>{message}</span>
</div>
