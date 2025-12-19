<script lang="ts">
	import { fade, scale } from 'svelte/transition';
	import WelcomeStep from './steps/WelcomeStep.svelte';
	import ApiKeyStep from './steps/ApiKeyStep.svelte';
	import ClusterStep from './steps/ClusterStep.svelte';
	import ReadyStep from './steps/ReadyStep.svelte';

	interface Props {
		onComplete: () => void;
	}

	let { onComplete }: Props = $props();

	let currentStep = $state(0);
	let hasCluster = $state(false);

	const steps = [
		{ id: 'welcome', label: 'Welcome' },
		{ id: 'api-key', label: 'API Key' },
		{ id: 'cluster', label: 'Cluster' },
		{ id: 'ready', label: 'Ready' }
	];

	function nextStep() {
		if (currentStep < steps.length - 1) {
			currentStep++;
		}
	}

	function prevStep() {
		if (currentStep > 0) {
			currentStep--;
		}
	}

	function skipCluster() {
		hasCluster = false;
		currentStep = 3; // Go to ready step
	}

	function clusterConnected() {
		hasCluster = true;
		nextStep();
	}

	function handleComplete() {
		onComplete();
	}

	// Handle escape key
	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape' && currentStep === steps.length - 1) {
			handleComplete();
		}
	}
</script>

<svelte:window onkeydown={handleKeydown} />

<!-- Modal backdrop -->
<div
	class="fixed inset-0 z-50 flex items-center justify-center p-4"
	transition:fade={{ duration: 200 }}
>
	<!-- Backdrop -->
	<div class="absolute inset-0 bg-black/80 backdrop-blur-sm"></div>

	<!-- Modal -->
	<div
		class="relative w-full max-w-lg bg-surface-900 rounded-2xl border border-surface-700/50 shadow-2xl overflow-hidden"
		transition:scale={{ duration: 200, start: 0.95 }}
	>
		<!-- Progress bar -->
		<div class="h-1 bg-surface-800">
			<div
				class="h-full bg-primary transition-all duration-300"
				style="width: {((currentStep + 1) / steps.length) * 100}%"
			></div>
		</div>

		<!-- Step indicators -->
		<div class="px-6 pt-6 pb-2">
			<div class="flex items-center justify-center gap-2">
				{#each steps as step, i}
					<div class="flex items-center">
						<div
							class="w-2 h-2 rounded-full transition-colors {i <= currentStep ? 'bg-primary' : 'bg-surface-700'}"
						></div>
						{#if i < steps.length - 1}
							<div class="w-8 h-px mx-1 {i < currentStep ? 'bg-primary' : 'bg-surface-700'}"></div>
						{/if}
					</div>
				{/each}
			</div>
			<p class="text-center text-xs text-surface-500 mt-2">
				Step {currentStep + 1} of {steps.length}
			</p>
		</div>

		<!-- Step content -->
		<div class="p-6 min-h-[400px]">
			{#if currentStep === 0}
				<WelcomeStep onNext={nextStep} />
			{:else if currentStep === 1}
				<ApiKeyStep onNext={nextStep} onBack={prevStep} />
			{:else if currentStep === 2}
				<ClusterStep onNext={clusterConnected} onBack={prevStep} onSkip={skipCluster} />
			{:else if currentStep === 3}
				<ReadyStep {hasCluster} onComplete={handleComplete} />
			{/if}
		</div>
	</div>
</div>
