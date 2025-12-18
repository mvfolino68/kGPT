<script lang="ts">
	import { StatusIndicator } from '$lib/components';

	interface Props {
		error: string;
	}

	let { error }: Props = $props();
</script>

<div class="bg-surface-900 border border-red-500/30 rounded-lg p-4">
	<div class="flex items-center gap-2.5 mb-3">
		<StatusIndicator status="error" size="md" />
		<span class="text-sm font-semibold text-red-400">Operation Failed</span>
	</div>
	<p class="text-sm text-red-300">{error}</p>
</div>
