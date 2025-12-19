<script lang="ts">
	// StatusIndicator - maintains backward compatibility with existing API
	import { StatusDot } from '$lib/components/ui';

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

	const statusMap = {
		active: 'success',
		inactive: 'inactive',
		warning: 'warning',
		error: 'error',
		info: 'info'
	} as const;
</script>

<StatusDot
	status={statusMap[status]}
	{size}
	{pulse}
	{label}
	class={className}
/>
