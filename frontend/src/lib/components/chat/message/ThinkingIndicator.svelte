<script lang="ts">
	import { StatusIndicator } from '$lib/components';

	interface Props {
		stage?: string;
	}

	let { stage = 'Processing...' }: Props = $props();
</script>

<div class="bg-surface-800 rounded-lg px-4 py-3 flex items-center gap-3">
	<div class="flex gap-1">
		<StatusIndicator status="active" pulse size="sm" />
		<StatusIndicator status="active" pulse size="sm" />
		<StatusIndicator status="active" pulse size="sm" />
	</div>
	<span class="text-sm text-surface-400">{stage}</span>
</div>

