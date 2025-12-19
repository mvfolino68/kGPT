<script lang="ts">
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
</script>

<SettingsCard title="OpenAI" status={hasApiKey ? 'saved' : null}>
	{#snippet icon()}
		<svg class="w-4 h-4 text-primary-light" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
			<path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
		</svg>
	{/snippet}

	<div class="space-y-4">
		<p class="text-sm text-surface-400">
			Powers AI responses for Kafka management queries.
		</p>

		<FormField label="API Key" id="openai-key">
			<input
				id="openai-key"
				type="password"
				value={apiKey}
				oninput={(e) => onapikeychange(e.currentTarget.value)}
				placeholder={hasApiKey ? '(leave empty to keep current)' : 'sk-...'}
				class="w-full input"
			/>
			<a
				href="https://platform.openai.com/api-keys"
				target="_blank"
				rel="noopener noreferrer"
				class="text-xs text-primary-light hover:underline mt-1.5 inline-block"
			>
				Get key at platform.openai.com/api-keys
			</a>
		</FormField>

		{#if validationError}
			<p class="text-sm text-red-400">{validationError}</p>
		{/if}

		<FormField label="Model" id="openai-model">
			<select
				id="openai-model"
				value={selectedModel}
				onchange={(e) => onmodelchange(e.currentTarget.value)}
				class="w-full input"
			>
				{#each models as model}
					<option value={model}>{model}</option>
				{/each}
			</select>
		</FormField>
	</div>

	{#snippet footer()}
		<button type="button" class="btn btn-primary" onclick={onsave} disabled={saving || validating}>
			{#if validating}
				Validating...
			{:else if saving}
				Saving...
			{:else}
				Save
			{/if}
		</button>
	{/snippet}
</SettingsCard>
