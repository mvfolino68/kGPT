<script lang="ts">
	import type { Snippet } from 'svelte';
	import { Button, Icon } from '$lib/components/ui';

	interface Props {
		title: string;
		count?: number;
		color?: 'blue' | 'amber' | 'emerald' | 'default';
		icon?: string;
		iconPath?: string;
		expanded?: boolean;
		class?: string;
		children: Snippet;
	}

	let {
		title,
		count,
		color = 'default',
		icon,
		iconPath,
		expanded = $bindable(false),
		class: className = '',
		children
	}: Props = $props();

	const colorClasses = {
		blue: {
			text: 'text-blue-400',
			bg: 'bg-blue-500/10',
			border: 'border-blue-500/20',
			hover: 'hover:border-blue-500/40'
		},
		amber: {
			text: 'text-amber-400',
			bg: 'bg-amber-500/10',
			border: 'border-amber-500/20',
			hover: 'hover:border-amber-500/40'
		},
		emerald: {
			text: 'text-emerald-400',
			bg: 'bg-emerald-500/10',
			border: 'border-emerald-500/20',
			hover: 'hover:border-emerald-500/40'
		},
		default: {
			text: 'text-surface-400',
			bg: 'bg-surface-500/10',
			border: 'border-surface-500/20',
			hover: 'hover:border-surface-500/40'
		}
	};

	const colors = colorClasses[color];

	function toggle() {
		expanded = !expanded;
	}
</script>

<div class="rounded-lg border {colors.border} {colors.hover} overflow-hidden transition-colors {className}">
	<Button
		variant="ghost"
		size="lg"
		class="w-full justify-between gap-3 p-3 rounded-none {colors.bg} hover:bg-opacity-70 transition-colors"
		onclick={toggle}
	>
		<div class="flex items-center gap-2">
			{#if iconPath}
				<svg class="w-4 h-4 {colors.text}" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d={iconPath} />
				</svg>
			{:else if icon}
				<Icon name={icon} size="sm" class={colors.text} />
			{/if}
			<span class="text-sm font-medium {colors.text}">{title}</span>
			{#if count !== undefined}
				<span class="text-xs text-surface-500">({count})</span>
			{/if}
		</div>

		<svg
			class="w-4 h-4 text-surface-500 transition-transform duration-150 {expanded ? 'rotate-180' : ''}"
			fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"
		>
			<path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
		</svg>
	</Button>

	{#if expanded}
		<div class="p-2 space-y-2 bg-surface-900/30">
			{@render children()}
		</div>
	{/if}
</div>
