<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { LoadingState } from '$lib/components';

	// Redirect to dashboard on mount
	onMount(() => {
		goto('/dashboard', { replaceState: true });
	});
</script>

<div class="flex items-center justify-center h-full bg-surface-900">
	<div class="text-center">
		<LoadingState
			message="Loading..."
			showSpinner={true}
			size="md"
			class="flex-col gap-4 text-surface-400 [&>svg]:text-primary"
		/>
	</div>
</div>
