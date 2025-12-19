<script lang="ts">
	type Status = 'success' | 'warning' | 'error' | 'inactive' | 'info';
	type Size = 'sm' | 'md' | 'lg';

	interface Props {
		status?: Status;
		size?: Size;
		pulse?: boolean;
		label?: string;
		class?: string;
	}

	let {
		status = 'inactive',
		size = 'md',
		pulse = false,
		label,
		class: className = ''
	}: Props = $props();
</script>

<div class="inline-flex items-center gap-2 {className}">
	<span
		class="
			rounded-full flex-shrink-0
			{size === 'sm' ? 'w-2 h-2' : size === 'lg' ? 'w-3 h-3' : 'w-2.5 h-2.5'}
			{status === 'success' ? 'bg-success' : ''}
			{status === 'warning' ? 'bg-warning' : ''}
			{status === 'error' ? 'bg-error' : ''}
			{status === 'info' ? 'bg-info' : ''}
			{status === 'inactive' ? 'bg-text-tertiary' : ''}
			{status === 'success' && !pulse ? 'shadow-[0_0_6px_rgba(52,211,153,0.40)]' : ''}
			{status === 'success' && pulse ? 'shadow-[0_0_10px_2px_rgba(52,211,153,0.50)] animate-pulse' : ''}
			{status === 'warning' && pulse ? 'shadow-[0_0_8px_2px_rgba(251,191,36,0.45)] animate-pulse' : ''}
			{status === 'error' && pulse ? 'shadow-[0_0_8px_2px_rgba(251,113,133,0.45)] animate-pulse' : ''}
			{status === 'info' && pulse ? 'shadow-[0_0_8px_2px_rgba(88,166,255,0.45)] animate-pulse' : ''}
		"
	></span>
	{#if label}
		<span class="text-sm text-text-secondary">{label}</span>
	{/if}
</div>
