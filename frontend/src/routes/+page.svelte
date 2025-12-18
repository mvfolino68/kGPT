<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';

	// Redirect to dashboard on mount
	onMount(() => {
		goto('/dashboard', { replaceState: true });
	});
</script>

<div class="flex items-center justify-center h-full bg-surface-900">
	<div class="text-center">
		<svg class="w-8 h-8 mx-auto text-primary animate-spin mb-4" fill="none" viewBox="0 0 24 24">
			<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
			<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
		</svg>
		<p class="text-surface-400 text-sm">Loading...</p>
	</div>
</div>
