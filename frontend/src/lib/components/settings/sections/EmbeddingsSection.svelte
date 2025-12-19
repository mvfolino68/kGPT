<script lang="ts">
	import { Button, Select, Icon } from '$lib/components/ui';
	import { SettingsCard, FormField } from '$lib/components/settings';

	interface Props {
		provider: string;
		model: string;
		saving: boolean;
		onsave: () => void;
		onproviderchange: (value: string) => void;
		onmodelchange: (value: string) => void;
	}

	let {
		provider,
		model,
		saving,
		onsave,
		onproviderchange,
		onmodelchange
	}: Props = $props();

	let providerValue = $state('');
	let modelValue = $state('');

	$effect(() => { providerValue = provider; });
	$effect(() => { modelValue = model; });

	const PROVIDERS = [
		{ value: 'fastembed', label: 'FastEmbed (Local)' },
		{ value: 'openai', label: 'OpenAI' }
	];

	const MODELS: Record<string, Array<{ value: string; label: string }>> = {
		fastembed: [
			{ value: 'BAAI/bge-small-en-v1.5', label: 'BAAI/bge-small-en-v1.5' },
			{ value: 'BAAI/bge-base-en-v1.5', label: 'BAAI/bge-base-en-v1.5' },
			{ value: 'snowflake/arctic-embed-m', label: 'snowflake/arctic-embed-m' }
		],
		openai: [
			{ value: 'text-embedding-3-small', label: 'text-embedding-3-small' },
			{ value: 'text-embedding-3-large', label: 'text-embedding-3-large' }
		]
	};
</script>

<SettingsCard title="Embeddings" status="saved">
	{#snippet icon()}
		<Icon name="database" size="sm" class="text-text-tertiary" />
	{/snippet}

	<div class="space-y-4">
		<p class="text-sm text-text-secondary">
			Configure the embedding model for document vectorization. FastEmbed runs locally, OpenAI requires your API key.
		</p>

		<div class="grid grid-cols-2 gap-4">
			<FormField label="Provider" id="embed-provider">
				<Select
					id="embed-provider"
					bind:value={providerValue}
					options={PROVIDERS}
					onchange={() => onproviderchange(providerValue)}
				/>
			</FormField>
			<FormField label="Model" id="embed-model">
				<Select
					id="embed-model"
					bind:value={modelValue}
					options={MODELS[providerValue] || []}
					onchange={() => onmodelchange(modelValue)}
				/>
			</FormField>
		</div>
	</div>

	{#snippet footer()}
		<Button variant="primary" onclick={onsave} disabled={saving} loading={saving}>
			Save
		</Button>
	{/snippet}
</SettingsCard>
