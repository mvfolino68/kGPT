<script lang="ts">
	import WizardStep from '../WizardStep.svelte';
	import kgptLogo from '$lib/assets/kgpt-logo.svg';

	interface Props {
		onNext: () => void;
	}

	let { onNext }: Props = $props();

	const features = [
		{
			icon: 'chat',
			title: 'Natural Language Kafka',
			description: 'Manage clusters with conversational AI'
		},
		{
			icon: 'brain',
			title: 'Multi-Agent RAG',
			description: 'Intelligent routing through specialized agents'
		},
		{
			icon: 'database',
			title: 'Vector Knowledge',
			description: 'Add docs to enhance AI responses'
		}
	];
</script>

<WizardStep title="Welcome to kGPT" subtitle="Your AI-powered Kafka management platform">
	{#snippet children()}
		<div class="flex flex-col items-center">
			<!-- Logo -->
			<div class="w-20 h-20 rounded-2xl bg-primary/10 flex items-center justify-center border border-primary/20 mb-8">
				<img src={kgptLogo} alt="kGPT" class="w-12 h-12" />
			</div>

			<!-- Features -->
			<div class="grid gap-4 w-full max-w-sm">
				{#each features as feature}
					<div class="flex items-start gap-4 p-4 rounded-lg bg-surface-800/50 border border-surface-700/50">
						<div class="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
							{#if feature.icon === 'chat'}
								<svg class="w-5 h-5 text-primary-light" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
									<path stroke-linecap="round" stroke-linejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
								</svg>
							{:else if feature.icon === 'brain'}
								<svg class="w-5 h-5 text-primary-light" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
									<path stroke-linecap="round" stroke-linejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
								</svg>
							{:else if feature.icon === 'database'}
								<svg class="w-5 h-5 text-primary-light" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
									<path stroke-linecap="round" stroke-linejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" />
								</svg>
							{/if}
						</div>
						<div>
							<h3 class="text-sm font-medium text-surface-100">{feature.title}</h3>
							<p class="text-xs text-surface-500 mt-0.5">{feature.description}</p>
						</div>
					</div>
				{/each}
			</div>
		</div>
	{/snippet}

	{#snippet actions()}
		<div class="flex justify-center">
			<button type="button" class="btn btn-primary px-8" onclick={onNext}>
				Get Started
			</button>
		</div>
	{/snippet}
</WizardStep>
