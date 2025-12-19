<script lang="ts">
	import { StatusPill } from '$lib/components/ui';

	type Status = 'active' | 'inactive' | 'warning' | 'error' | 'info';

	interface Props {
		status: Status;
		label: string;
		sublabel?: string;
		pulse?: boolean;
	}

	let { status, label, sublabel, pulse = false }: Props = $props();

	const statusMap = {
		active: 'success',
		inactive: 'inactive',
		warning: 'warning',
		error: 'error',
		info: 'info'
	} as const;
</script>

<StatusPill
	status={statusMap[status]}
	label={label}
	sublabel={sublabel}
	pulse={pulse}
/>
