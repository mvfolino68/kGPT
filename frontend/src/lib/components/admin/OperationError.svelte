<script lang="ts">
	import { Card, StatusPill } from '$lib/components/ui';

	interface Props {
		error: string;
	}

	let { error }: Props = $props();
</script>

<Card variant="glass" class="bg-surface-900 ring-0 border border-error/30">
	<div class="flex items-center gap-2.5 mb-3">
		<StatusPill status="error" size="sm" label="Failed" />
		<span class="text-sm font-semibold text-red-400">Operation Failed</span>
	</div>
	<p class="text-sm text-red-300">{error}</p>
</Card>
