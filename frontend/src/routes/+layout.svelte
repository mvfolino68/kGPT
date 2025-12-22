<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { refreshHealth } from '$lib/stores/health';
	import { checkOnboarding, getOnboardingState, completeOnboarding } from '$lib/stores/onboarding.svelte';
	import { Sidebar } from '$lib/components/layout';
	import { OnboardingWizard } from '$lib/components/onboarding';
	import { SourceDrawer } from '$lib/components/sources';
	import { selectedGlobalSource, closeSourceDrawer, chatMessages } from '$lib/stores/chat';

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

	// Global click handler for citations
	function handleGlobalClick(event: MouseEvent) {
		const target = event.target as HTMLElement;
		if (target.classList.contains('citation-ref')) {
			const index = parseInt(target.dataset.citationIndex || '0', 10);
			// Find the message that contains this citation
			// We look for the closest message container to know which message's sources to use
			const messageEl = target.closest('[data-message-id]');
			if (messageEl && messageEl instanceof HTMLElement) {
				const messageId = messageEl.dataset.messageId;
				const message = $chatMessages.find(m => m.id === messageId);
				if (message && message.citations && index > 0 && index <= message.citations.length) {
					const citation = message.citations[index - 1];
					// Import normalizeCitation dynamically or move it to a shared util that we can import here?
					// Ideally we should have normalized sources available.
					// For now, let's assume specific structure or import the helper.
					// We'll trust the SourceDrawer to handle the citation object, or normalizing it here.
					// Better: use the helper.
					import('$lib/components/sources/types').then(({ normalizeCitation }) => {
						selectedGlobalSource.set(normalizeCitation(citation));
					});
				}
			}
		}
	}
</script>

<svelte:window onclick={handleGlobalClick} />

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

<!-- Global Source Drawer -->
<SourceDrawer source={$selectedGlobalSource} onClose={closeSourceDrawer} />
