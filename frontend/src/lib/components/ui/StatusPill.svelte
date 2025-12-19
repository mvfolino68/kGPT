<script lang="ts">
	import StatusDot from './StatusDot.svelte';

	type Status = 'success' | 'warning' | 'error' | 'inactive' | 'info';
	type Size = 'sm' | 'md';

	interface Props {
		status?: Status;
		size?: Size;
		pulse?: boolean;
		label: string;
		sublabel?: string;
		class?: string;
	}

	let {
		status = 'inactive',
		size = 'sm',
		pulse = false,
		label,
		sublabel,
		class: className = ''
	}: Props = $props();

	const toneClasses = $derived(() => {
		// Use the more visible "badge" tone (green is good), but without borders
		if (status === 'success') return 'bg-success/15 text-success';
		if (status === 'warning') return 'bg-warning/15 text-warning';
		if (status === 'error') return 'bg-error/15 text-error';
		if (status === 'info') return 'bg-info/15 text-info';
		return 'bg-surface-hover text-text-secondary';
	});

	const sizeClasses = $derived(() => {
		return size === 'md' ? 'text-xs px-2.5 py-1' : 'text-[10px] px-2 py-0.5';
	});
</script>

<span
	class="
		inline-flex items-center gap-1.5 rounded-full
		{toneClasses()}
		{sizeClasses()}
		{className}
	"
>
	<StatusDot status={status} size="sm" pulse={pulse} />
	<span class="min-w-0 inline-flex items-center gap-1.5">
		<span class="truncate">{label}</span>
		{#if sublabel}
			<span class="text-current/70 font-normal truncate">
				{sublabel}
			</span>
		{/if}
	</span>
</span>

