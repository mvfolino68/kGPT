<script lang="ts">
	import { Button, Input, Select, Icon } from '$lib/components/ui';
	import { SettingsCard, FormField } from '$lib/components/settings';

	interface Props {
		source: 'env' | 'db' | null;
		models: string[];
		selectedModel: string;
		apiKey: string;
		hasApiKey: boolean;
		saving: boolean;
		validating: boolean;
		validationError: string | null;
		onsave: () => void;
		onmodelchange: (model: string) => void;
		onapikeychange: (value: string) => void;
	}

	let {
		source,
		models,
		selectedModel,
		apiKey,
		hasApiKey,
		saving,
		validating,
		validationError,
		onsave,
		onmodelchange,
		onapikeychange
	}: Props = $props();

	let apiKeyValue = $state('');
	let modelValue = $state('');

	$effect(() => { apiKeyValue = apiKey; });
	$effect(() => { modelValue = selectedModel; });
</script>

<SettingsCard title="OpenAI" status={hasApiKey ? 'saved' : null}>
	{#snippet icon()}
		<Icon name="sparkles" size="sm" class="text-text-tertiary" />
	{/snippet}

	<div class="space-y-4">
		<p class="text-sm text-text-secondary">
			Powers AI responses for Kafka management queries.
		</p>

		<FormField label="API Key" id="openai-key">
			<Input
				id="openai-key"
				type="password"
				bind:value={apiKeyValue}
				oninput={() => onapikeychange(apiKeyValue)}
				placeholder={hasApiKey ? '(leave empty to keep current)' : 'sk-...'}
			/>
			<a
				href="https://platform.openai.com/api-keys"
				target="_blank"
				rel="noopener noreferrer"
				class="text-xs text-text-tertiary hover:text-text-secondary hover:underline mt-1.5 inline-block"
			>
				Get key at platform.openai.com/api-keys
			</a>
		</FormField>

		{#if validationError}
			<p class="text-sm text-error">{validationError}</p>
		{/if}

		<FormField label="Model" id="openai-model">
			<Select
				id="openai-model"
				bind:value={modelValue}
				options={models}
				onchange={() => onmodelchange(modelValue)}
			/>
		</FormField>
	</div>

	{#snippet headerAction()}
		<Button variant="primary" size="sm" onclick={onsave} disabled={saving || validating} loading={saving || validating}>
			Save
		</Button>
	{/snippet}
</SettingsCard>
