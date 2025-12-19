<script lang="ts">
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
</script>

<SettingsCard title="Web Search (Exa)" status={hasApiKey ? 'saved' : null}>
	{#snippet icon()}
		<svg class="w-4 h-4 text-surface-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
			<path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
		</svg>
	{/snippet}

	<div class="space-y-4">
		<p class="text-sm text-surface-400">
			Enable real-time web search to fetch current information during queries.
		</p>

		<FormField label="Exa API Key" id="exa-key">
			<input
				id="exa-key"
				type="password"
				value={apiKey}
				oninput={(e) => onapikeychange(e.currentTarget.value)}
				placeholder={hasApiKey ? '(leave empty to keep current)' : 'exa-...'}
				class="w-full input"
			/>
			<a
				href="https://dashboard.exa.ai/api-keys"
				target="_blank"
				rel="noopener noreferrer"
				class="text-xs text-surface-400 hover:text-surface-300 hover:underline mt-1.5 inline-block"
			>
				Get key at dashboard.exa.ai/api-keys
			</a>
		</FormField>
	</div>

	{#snippet footer()}
		<button type="button" class="btn btn-primary" onclick={onsave} disabled={saving || !apiKey.trim()}>
			{saving ? 'Saving...' : 'Save'}
		</button>
	{/snippet}
</SettingsCard>
