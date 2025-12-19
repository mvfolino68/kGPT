<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { refreshHealth } from '$lib/stores/health';
	import { checkOnboarding, getOnboardingState, completeOnboarding } from '$lib/stores/onboarding.svelte';
	import { Sidebar } from '$lib/components/layout';
	import { OnboardingWizard } from '$lib/components/onboarding';

	let { children } = $props();

	let ready = $state(false);
	let onboardingState = getOnboardingState();

	onMount(() => {
		(async () => {
			// Check onboarding status
			await checkOnboarding();

			// Quick fade-in after check
			setTimeout(() => { ready = true; }, 100);
		})().catch(() => {
			// Even if onboarding check fails, don't block the UI
			setTimeout(() => { ready = true; }, 100);
		});

		refreshHealth();
		const interval = setInterval(refreshHealth, 30000);
		return () => clearInterval(interval);
	});

	function handleOnboardingComplete() {
		completeOnboarding();
	}
</script>

<svelte:head>
	<title>kGPT - Kafka Management Platform</title>
	<link rel="icon" type="image/svg+xml" href="/favicon.svg" />
</svelte:head>

<div class="flex h-screen bg-bg {ready ? 'opacity-100' : 'opacity-0'}" style="transition: opacity 150ms ease">
	<Sidebar />

	<main class="flex-1 overflow-hidden">
		{@render children()}
	</main>
</div>

<!-- Onboarding Wizard Modal -->
{#if onboardingState.showWizard}
	<OnboardingWizard onComplete={handleOnboardingComplete} />
{/if}
