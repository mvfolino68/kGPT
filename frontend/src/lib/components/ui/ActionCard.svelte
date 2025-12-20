<script lang="ts">
	import Icon from './Icon.svelte';

	interface Props {
		icon: string;
		title: string;
		description?: string;
		onclick?: () => void;
		disabled?: boolean;
		loading?: boolean;
		variant?: 'default' | 'primary';
		class?: string;
	}

	let {
		icon,
		title,
		description,
		onclick,
		disabled = false,
		loading = false,
		variant = 'default',
		class: className = ''
	}: Props = $props();

	const variantClasses = {
		default: 'bg-surface hover:bg-surface-hover',
		primary: 'bg-primary/10 hover:bg-primary/20'
	};

	const iconBgClasses = {
		default: 'bg-surface-active',
		primary: 'bg-primary/20'
	};

	const iconTextClasses = {
		default: 'text-text-secondary',
		primary: 'text-primary'
	};
</script>

<button
	type="button"
	class="w-full flex items-center gap-3 p-3 rounded-lg text-left transition-all duration-200 group
		{variantClasses[variant]} {disabled ? 'opacity-50 cursor-not-allowed' : ''} {className}"
	{onclick}
	{disabled}
>
	<div class="w-10 h-10 rounded-lg {iconBgClasses[variant]} flex items-center justify-center shrink-0
		group-hover:scale-105 transition-transform">
		{#if loading}
			<Icon name="loader-2" size="md" class="{iconTextClasses[variant]} animate-spin" />
		{:else}
			<Icon name={icon} size="md" class={iconTextClasses[variant]} />
		{/if}
	</div>
	<div class="flex-1 min-w-0">
		<span class="text-sm font-medium text-text block">{title}</span>
		{#if description}
			<span class="text-xs text-text-tertiary block mt-0.5 truncate">{description}</span>
		{/if}
	</div>
	{#if onclick && !loading}
		<Icon name="chevron-right" size="sm" class="text-text-tertiary group-hover:text-text-secondary transition-colors" />
	{/if}
</button>
