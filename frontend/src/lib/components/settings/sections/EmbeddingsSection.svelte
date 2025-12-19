<script lang="ts">
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

	const PROVIDERS = [
		{ value: 'fastembed', label: 'FastEmbed (Local)' },
		{ value: 'openai', label: 'OpenAI' }
	];

	const MODELS: Record<string, string[]> = {
		fastembed: ['BAAI/bge-small-en-v1.5', 'BAAI/bge-base-en-v1.5', 'snowflake/arctic-embed-m'],
		openai: ['text-embedding-3-small', 'text-embedding-3-large']
	};
</script>

<SettingsCard title="Embeddings" status="saved">
	{#snippet icon()}
		<svg class="w-4 h-4 text-surface-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
			<path stroke-linecap="round" stroke-linejoin="round" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
		</svg>
	{/snippet}

	<div class="space-y-4">
		<p class="text-sm text-surface-400">
			Configure the embedding model for document vectorization. FastEmbed runs locally, OpenAI requires your API key.
		</p>

		<div class="grid grid-cols-2 gap-4">
			<FormField label="Provider" id="embed-provider">
				<select
					id="embed-provider"
					value={provider}
					onchange={(e) => onproviderchange(e.currentTarget.value)}
					class="w-full input"
				>
					{#each PROVIDERS as p}
						<option value={p.value}>{p.label}</option>
					{/each}
				</select>
			</FormField>
			<FormField label="Model" id="embed-model">
				<select
					id="embed-model"
					value={model}
					onchange={(e) => onmodelchange(e.currentTarget.value)}
					class="w-full input"
				>
					{#each MODELS[provider] || [] as m}
						<option value={m}>{m}</option>
					{/each}
				</select>
			</FormField>
		</div>
	</div>

	{#snippet footer()}
		<button type="button" class="btn btn-primary" onclick={onsave} disabled={saving}>
			{saving ? 'Saving...' : 'Save'}
		</button>
	{/snippet}
</SettingsCard>
