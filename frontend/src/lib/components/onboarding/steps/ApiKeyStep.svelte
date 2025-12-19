<script lang="ts">
	import { Button } from '$lib/components/ui';
	import WizardStep from '../WizardStep.svelte';
	import { validateApiKey, updateSettings } from '$lib/api';
	import { StatusIndicator } from '$lib/components';

	interface Props {
		onNext: () => void;
		onBack: () => void;
	}

	let { onNext, onBack }: Props = $props();

	let apiKey = $state('');
	let validating = $state(false);
	let saving = $state(false);
	let error = $state<string | null>(null);
	let models = $state<string[]>([]);
	let selectedModel = $state('');

	async function handleValidate() {
		if (!apiKey.trim()) return;

		validating = true;
		error = null;

		try {
			const result = await validateApiKey('openai', apiKey.trim());
			if (result.valid) {
				models = result.models;
				selectedModel = result.models[0] || '';
			} else {
				error = result.message || 'Invalid API key';
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Validation failed';
		} finally {
			validating = false;
		}
	}

	async function handleSaveAndContinue() {
		if (!apiKey.trim() || !selectedModel) return;

		saving = true;
		error = null;

		try {
			await updateSettings({
				llm_provider: 'openai',
				llm_model: selectedModel,
				openai_api_key: apiKey.trim()
			});
			onNext();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to save';
		} finally {
			saving = false;
		}
	}
</script>

<WizardStep
	title="Connect OpenAI"
	subtitle="Enter your API key to power the AI assistant"
>
	{#snippet children()}
		<div class="max-w-sm mx-auto space-y-6">
			<!-- API Key Input -->
			<div>
				<label for="api-key" class="block text-xs font-medium uppercase tracking-wider text-surface-500 mb-2">
					OpenAI API Key
				</label>
				<input
					id="api-key"
					type="password"
					bind:value={apiKey}
					placeholder="sk-..."
					disabled={models.length > 0}
					class="w-full bg-surface-700/50 border-none rounded-md px-3 py-2 text-sm text-foreground placeholder:text-muted transition-all focus:outline-none focus:bg-surface-700 focus:ring-2 focus:ring-primary-600/50"
				/>
				<a
					href="https://platform.openai.com/api-keys"
					target="_blank"
					rel="noopener noreferrer"
					class="text-xs text-primary-light hover:underline mt-2 inline-block"
				>
					Get your API key from OpenAI
				</a>
			</div>

			<!-- Error -->
			{#if error}
				<div class="flex items-center gap-2 text-sm text-red-400">
					<StatusIndicator status="error" size="sm" />
					<span>{error}</span>
				</div>
			{/if}

			<!-- Validate Button -->
			{#if models.length === 0}
				<Button
					variant="primary"
					class="w-full"
					onclick={handleValidate}
					disabled={validating || !apiKey.trim()}
					loading={validating}
				>
					Validate Key
				</Button>
			{:else}
				<!-- Model Selection -->
				<div class="space-y-4 pt-4 border-t border-surface-700/50">
					<div class="flex items-center gap-2 text-sm text-emerald-400">
						<StatusIndicator status="active" size="sm" />
						<span>API key validated</span>
					</div>

					<div>
						<label for="model-select" class="block text-xs font-medium uppercase tracking-wider text-surface-500 mb-2">
							Select Model
						</label>
						<select id="model-select" bind:value={selectedModel} class="w-full input">
							{#each models as model}
								<option value={model}>{model}</option>
							{/each}
						</select>
					</div>
				</div>
			{/if}
		</div>
	{/snippet}

	{#snippet actions()}
		<div class="flex justify-between">
			<Button variant="ghost" onclick={onBack}>
				Back
			</Button>
			<Button
				variant="primary"
				class="px-6"
				onclick={handleSaveAndContinue}
				disabled={saving || models.length === 0 || !selectedModel}
				loading={saving}
			>
				Continue
			</Button>
		</div>
	{/snippet}
</WizardStep>
