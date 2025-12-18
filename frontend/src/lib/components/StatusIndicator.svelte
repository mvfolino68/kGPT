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
		active: 'led-green',
		inactive: 'led-off',
		warning: 'led-amber',
		error: 'led-red',
		info: 'led-cyan'
	};

	const sizeClasses = {
		sm: 'w-2 h-2',
		md: 'led-indicator',
		lg: 'led-large'
	};
</script>

<div class="inline-flex items-center gap-2 {className}">
	<span class="{sizeClasses[size]} {statusColors[status]} rounded-full {pulse ? 'animate-glow-pulse' : ''}" />
	{#if label}
		<span class="text-sm font-mono text-surface-400">{label}</span>
	{/if}
</div>
