<script lang="ts">
	interface Props {
		status: 'success' | 'warning' | 'error' | 'inactive' | 'info';
		size?: 'sm' | 'md' | 'lg';
		pulse?: boolean;
		class?: string;
	}

	let {
		status = 'inactive',
		size = 'md',
		pulse = false,
		class: className = ''
	}: Props = $props();

	const statusClasses = {
		success: 'status-dot-success',
		warning: 'status-dot-warning',
		error: 'status-dot-error',
		inactive: 'status-dot-inactive',
		info: 'bg-blue-500'
	};

	const sizeClasses = {
		sm: 'w-1.5 h-1.5',
		md: 'status-dot',
		lg: 'status-dot status-dot-lg'
	};
</script>

<span class="{sizeClasses[size]} {statusClasses[status]} {pulse ? 'status-dot-pulse' : ''} rounded-full flex-shrink-0 {className}"></span>
