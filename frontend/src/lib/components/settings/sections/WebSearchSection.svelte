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

<SettingsCard title="Web Search (Exa)" status={hasApiKey ? 'saved' : null}>
	{#snippet icon()}
		<Icon name="search" size="sm" class="text-text-tertiary" />
	{/snippet}

	<div class="space-y-4">
		<p class="text-sm text-text-secondary">
			Enable real-time web search to fetch current information during queries.
		</p>

		<FormField label="Exa API Key" id="exa-key">
			<Input
				id="exa-key"
				type="password"
				bind:value={apiKeyValue}
				oninput={() => onapikeychange(apiKeyValue)}
				placeholder={hasApiKey ? '(leave empty to keep current)' : 'exa-...'}
			/>
			<a
				href="https://dashboard.exa.ai/api-keys"
				target="_blank"
				rel="noopener noreferrer"
				class="text-xs text-text-tertiary hover:text-text-secondary hover:underline mt-1.5 inline-block"
			>
				Get key at dashboard.exa.ai/api-keys
			</a>
		</FormField>
	</div>

	{#snippet headerAction()}
		<Button variant="primary" size="sm" onclick={onsave} disabled={saving || !apiKeyValue.trim()} loading={saving}>
			Save
		</Button>
	{/snippet}
</SettingsCard>
