<script lang="ts">
	import { Button, Input, Icon } from '$lib/components/ui';
	import { SettingsCard, FormField } from '$lib/components/settings';

	interface Props {
		apiKey: string;
		hasApiKey: boolean;
		saving: boolean;
		onsave: () => void;
		onapikeychange: (value: string) => void;
	}

	let {
		apiKey,
		hasApiKey,
		saving,
		onsave,
		onapikeychange
	}: Props = $props();

	let apiKeyValue = $state('');

	$effect(() => { apiKeyValue = apiKey; });
</script>

<SettingsCard title="Reranking (Cohere)" status={hasApiKey ? 'saved' : null}>
	{#snippet icon()}
		<svg class="w-4 h-4 text-text-tertiary" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
			<path stroke-linecap="round" stroke-linejoin="round" d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12" />
		</svg>
	{/snippet}

	<div class="space-y-4">
		<p class="text-sm text-text-secondary">
			Cohere reranking improves retrieval quality by reordering search results.
		</p>

		<FormField label="Cohere API Key" id="cohere-key">
			<Input
				id="cohere-key"
				type="password"
				bind:value={apiKeyValue}
				oninput={() => onapikeychange(apiKeyValue)}
				placeholder={hasApiKey ? '(leave empty to keep current)' : 'your-cohere-key'}
			/>
			<a
				href="https://dashboard.cohere.com/api-keys"
				target="_blank"
				rel="noopener noreferrer"
				class="text-xs text-text-tertiary hover:text-text-secondary hover:underline mt-1.5 inline-block"
			>
				Get key at dashboard.cohere.com/api-keys
			</a>
		</FormField>
	</div>

	{#snippet footer()}
		<Button variant="primary" onclick={onsave} disabled={saving || !apiKeyValue.trim()} loading={saving}>
			Save
		</Button>
	{/snippet}
</SettingsCard>
