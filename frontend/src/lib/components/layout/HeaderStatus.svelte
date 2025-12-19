<script lang="ts">
	import StatusIndicator from '../StatusIndicator.svelte';

	interface Props {
		status: 'active' | 'inactive' | 'warning' | 'error' | 'info';
		label: string;
		sublabel?: string;
		pulse?: boolean;
	}

	let { status, label, sublabel, pulse = false }: Props = $props();
</script>

<div class="flex items-center gap-2 text-xs">
	<StatusIndicator {status} size="sm" {pulse} />
	<span class="text-surface-400">{label}</span>
	{#if sublabel}
		<span class="text-surface-200 font-medium">{sublabel}</span>
	{/if}
</div>
