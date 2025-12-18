<script lang="ts">
	interface Props {
		status: 'active' | 'inactive' | 'warning' | 'error' | 'info';
		size?: 'sm' | 'md' | 'lg';
		pulse?: boolean;
		label?: string;
		class?: string;
	}

	let {
		status,
		size = 'md',
		pulse = false,
		label,
		class: className = ''
	}: Props = $props();

	const statusColors = {
		active: 'bg-emerald-500',
		inactive: 'bg-surface-600',
		warning: 'bg-amber-500',
		error: 'bg-red-500',
		info: 'bg-blue-500'
	};

	const sizeClasses = {
		sm: 'w-1.5 h-1.5',
		md: 'w-2 h-2',
		lg: 'w-2.5 h-2.5'
	};
</script>

<div class="inline-flex items-center gap-2 {className}">
	<span class="{sizeClasses[size]} {statusColors[status]} rounded-full flex-shrink-0 {pulse ? 'status-dot-pulse' : ''}"></span>
	{#if label}
		<span class="text-sm text-surface-400">{label}</span>
	{/if}
</div>

