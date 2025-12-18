<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { refreshHealth } from '$lib/stores/health';
	import { Sidebar } from '$lib/components/layout';

	let { children } = $props();

	let ready = $state(false);

	onMount(() => {
		// Quick fade-in
		setTimeout(() => { ready = true; }, 100);

		refreshHealth();
		const interval = setInterval(refreshHealth, 30000);
		return () => clearInterval(interval);
	});
</script>

<svelte:head>
	<title>kGPT - Kafka Management Platform</title>
	<link rel="icon" type="image/svg+xml" href="/favicon.svg" />
</svelte:head>

<div class="flex h-screen bg-surface-900 {ready ? 'opacity-100' : 'opacity-0'}" style="transition: opacity 150ms ease">
	<Sidebar />

	<main class="flex-1 overflow-hidden">
		{@render children()}
	</main>
</div>
