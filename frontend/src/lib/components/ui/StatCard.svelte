<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		label: string;
		value?: string | number | null;
		unit?: string;
		size?: 'sm' | 'md' | 'lg';
		variant?: 'default' | 'success' | 'warning';
		trend?: 'up' | 'down' | 'neutral';
		class?: string;
		children?: Snippet;
	}

	let {
		label,
		value,
		unit,
		size = 'md',
		variant = 'default',
		trend,
		class: className = '',
		children
	}: Props = $props();

	const sizeClasses = {
		sm: { container: 'p-2', value: 'text-lg', label: 'text-[9px]' },
		md: { container: 'p-3', value: 'text-xl', label: 'text-[10px]' },
		lg: { container: 'p-4', value: 'text-2xl', label: 'text-xs' }
	};

	const variantClasses = {
		default: 'text-surface-200',
		success: 'text-emerald-400/80',
		warning: 'text-amber-400/80'
	};

	const trendIcons = {
		up: '↑',
		down: '↓',
		neutral: '→'
	};

	const trendColors = {
		up: 'text-emerald-400',
		down: 'text-red-400',
		neutral: 'text-surface-400'
	};
</script>

<div class="inner-card {sizeClasses[size].container} {className}">
	<div class="{sizeClasses[size].label} font-bold uppercase tracking-wider text-surface-500 mb-1">
		{label}
	</div>
	<div class="flex flex-col">
		<div class="flex items-baseline gap-1.5">
			<span class="{sizeClasses[size].value} {variantClasses[variant]}">
				{value ?? '—'}
			</span>
			{#if unit}
				<span class="text-xs text-surface-500">{unit}</span>
			{/if}
			{#if trend}
				<span class="text-sm {trendColors[trend]}">{trendIcons[trend]}</span>
			{/if}
		</div>
		{#if children}
			{@render children()}
		{/if}
	</div>
</div>
