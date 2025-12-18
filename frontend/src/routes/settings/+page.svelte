<script lang="ts">
	import { onMount } from 'svelte';
	import {
		getSettings,
		updateSettings,
		validateApiKey,
		type Settings,
		type KeyStatus
	} from '$lib/api';
	import { RetroHeader, RetroButton, RetroCard, StatusIndicator } from '$lib/components';

	let settings = $state<Settings | null>(null);
	let loading = $state(true);
	let saving = $state(false);
	let error = $state<string | null>(null);
	let success = $state<string | null>(null);

	// OpenAI state
	let openaiConfigured = $state(false);
	let openaiSource = $state<'env' | 'db' | null>(null);
	let openaiValid = $state(false);
	let openaiValidating = $state(false);
	let openaiModels = $state<string[]>([]);
	let openaiSelectedModel = $state('');
	let openaiError = $state<string | null>(null);

	// For adding/updating OpenAI key
	let showAddKey = $state(false);
	let isUpdatingKey = $state(false);
	let newKeyInput = $state('');
	let newKeyValidating = $state(false);
	let newKeyError = $state<string | null>(null);
	let newKeyModels = $state<string[]>([]);
	let newKeySelectedModel = $state('');

	// Embedding settings
	let embeddingProvider = $state('fastembed');
	let embeddingModel = $state('BAAI/bge-small-en-v1.5');
	let huggingFaceToken = $state('');
	let hasHuggingFaceToken = $state(false);

	// Exa web search settings
	let exaApiKey = $state('');
	let hasExaApiKey = $state(false);
	let webSearchEnabled = $state(true);

	// Cohere reranking settings
	let cohereApiKey = $state('');
	let hasCohereApiKey = $state(false);

	// Onboarding
	let isOnboarding = $state(false);

	const EMBEDDING_PROVIDERS = [
		{ value: 'fastembed', label: 'FastEmbed (Local)' },
		{ value: 'openai', label: 'OpenAI' }
	];

	const EMBEDDING_MODELS: Record<string, string[]> = {
		fastembed: ['BAAI/bge-small-en-v1.5', 'BAAI/bge-base-en-v1.5', 'snowflake/arctic-embed-m'],
		openai: ['text-embedding-3-small', 'text-embedding-3-large']
	};

	async function loadSettings() {
		loading = true;
		error = null;

		try {
			settings = await getSettings();
			openaiSelectedModel = settings.llm_model || '';
			embeddingProvider = settings.embedding_provider || 'fastembed';
			embeddingModel = settings.embedding_model || 'BAAI/bge-small-en-v1.5';
			hasHuggingFaceToken = settings.has_huggingface_token || false;
			hasCohereApiKey = settings.has_cohere_key || false;
			hasExaApiKey = settings.has_exa_key || false;
			webSearchEnabled = settings.web_search_enabled ?? true;

			// Check if OpenAI is configured
			if (settings.openai_key?.configured) {
				openaiConfigured = true;
				openaiSource = settings.openai_key.source;
				await validateOpenAI();
			}

			if (!openaiConfigured || !openaiValid) {
				isOnboarding = true;
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load settings';
		} finally {
			loading = false;
		}
	}

	async function validateOpenAI() {
		openaiValidating = true;
		openaiError = null;

		try {
			const result = await validateApiKey('openai', '__USE_STORED__');
			openaiValid = result.valid;
			openaiModels = result.models;
			if (result.models.length > 0) {
				openaiSelectedModel = result.models.includes(openaiSelectedModel)
					? openaiSelectedModel
					: result.models[0];
			}
			openaiError = result.valid ? null : result.message;
		} catch (e) {
			openaiValid = false;
			openaiError = e instanceof Error ? e.message : 'Validation failed';
		} finally {
			openaiValidating = false;
		}
	}

	async function validateNewKey() {
		if (!newKeyInput.trim()) return;
		newKeyValidating = true;
		newKeyError = null;

		try {
			const result = await validateApiKey('openai', newKeyInput.trim());
			if (result.valid) {
				newKeyModels = result.models;
				newKeySelectedModel = result.models[0] || '';
			} else {
				newKeyError = result.message || 'Invalid key';
			}
		} catch (e) {
			newKeyError = e instanceof Error ? e.message : 'Failed';
		} finally {
			newKeyValidating = false;
		}
	}

	async function saveNewKey() {
		if (!newKeyInput.trim() || !newKeySelectedModel) return;
		saving = true;

		try {
			await updateSettings({
				llm_provider: 'openai',
				llm_model: newKeySelectedModel,
				openai_api_key: newKeyInput.trim()
			});
			openaiConfigured = true;
			openaiSource = 'db';
			openaiValid = true;
			openaiModels = newKeyModels;
			openaiSelectedModel = newKeySelectedModel;
			success = 'OpenAI API key saved!';
			cancelAddKey();
			isOnboarding = false;
			setTimeout(() => { success = null; }, 2000);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed';
		} finally {
			saving = false;
		}
	}

	function cancelAddKey() {
		showAddKey = false;
		isUpdatingKey = false;
		newKeyInput = '';
		newKeyError = null;
		newKeyModels = [];
		newKeySelectedModel = '';
	}

	function startUpdateKey() {
		showAddKey = true;
		isUpdatingKey = true;
		newKeyInput = '';
		newKeyError = null;
		newKeyModels = [];
		newKeySelectedModel = '';
	}

	async function updateModel() {
		if (!openaiSelectedModel) return;

		saving = true;
		try {
			await updateSettings({ llm_model: openaiSelectedModel });
			success = 'Model updated';
			setTimeout(() => { success = null; }, 2000);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed';
		} finally {
			saving = false;
		}
	}

	async function saveEmbeddingSettings() {
		saving = true;
		try {
			const updates: Partial<Settings> = {
				embedding_provider: embeddingProvider,
				embedding_model: embeddingModel
			};
			if (huggingFaceToken.trim()) {
				updates.huggingface_token = huggingFaceToken.trim();
			}
			await updateSettings(updates);
			hasHuggingFaceToken = hasHuggingFaceToken || !!huggingFaceToken.trim();
			huggingFaceToken = '';
			success = 'Embedding settings saved';
			setTimeout(() => { success = null; }, 2000);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed';
		} finally {
			saving = false;
		}
	}

	async function saveExaSettings() {
		saving = true;
		try {
			const updates: Partial<Settings> = { web_search_enabled: webSearchEnabled };
			if (exaApiKey.trim()) {
				updates.exa_api_key = exaApiKey.trim();
			}
			await updateSettings(updates);
			hasExaApiKey = hasExaApiKey || !!exaApiKey.trim();
			exaApiKey = '';
			success = 'Web search settings saved';
			setTimeout(() => { success = null; }, 2000);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed';
		} finally {
			saving = false;
		}
	}

	async function saveCohereSettings() {
		saving = true;
		try {
			if (cohereApiKey.trim()) {
				await updateSettings({ cohere_api_key: cohereApiKey.trim() });
				hasCohereApiKey = true;
				cohereApiKey = '';
				success = 'Cohere API key saved';
				setTimeout(() => { success = null; }, 2000);
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed';
		} finally {
			saving = false;
		}
	}

	onMount(() => { loadSettings(); });
</script>

<div class="flex flex-col h-full bg-surface-950">
	<RetroHeader path="kgpt/settings" flag="--configure">
		{#snippet rightContent()}
			{#if openaiValid && openaiSelectedModel && !isOnboarding}
				<div class="px-3 py-1.5 retro-card-glow-blue rounded font-mono text-xs flex items-center gap-2">
					<StatusIndicator status="active" size="sm" pulse />
					<span class="text-surface-500">active:</span>
					<span class="text-confluent-primary">openai/{openaiSelectedModel}</span>
				</div>
			{/if}
		{/snippet}
	</RetroHeader>

	<div class="flex-1 overflow-y-auto p-6">
		<div class="max-w-4xl mx-auto space-y-6">
			<!-- Messages -->
			{#if error}
				<div class="retro-card-glow-amber rounded p-3 font-mono text-sm text-red-400 flex items-center gap-2">
					<StatusIndicator status="error" size="sm" />
					<span class="text-red-500">error:</span> {error}
				</div>
			{/if}
			{#if success}
				<div class="retro-card-glow-green rounded p-3 font-mono text-sm text-emerald-400 flex items-center gap-2">
					<StatusIndicator status="active" size="sm" />
					<span class="text-emerald-500">ok</span> {success}
				</div>
			{/if}

			{#if loading}
				<RetroCard>
					<div class="p-8 text-center font-mono text-surface-500 animate-pulse-slow flex items-center justify-center gap-2">
						<StatusIndicator status="warning" pulse />
						loading...
					</div>
				</RetroCard>

			{:else if isOnboarding && !openaiValid}
				<!-- ONBOARDING -->
				<div class="space-y-6">
				<RetroCard variant="glow-blue" class="text-center py-6">
					<h2 class="text-2xl font-bold font-mono text-confluent-primary mb-2 text-glow-blue">WELCOME TO kGPT</h2>
					<p class="text-surface-400 font-mono text-sm">Configure your OpenAI API key to get started</p>
				</RetroCard>

					<RetroCard variant="glow-cyan">
						<div class="space-y-4">
							<div>
								<label for="api-key" class="block text-xs font-mono text-surface-500 mb-1 uppercase tracking-wider">OpenAI API Key</label>
								<input
									id="api-key"
									type="password"
									bind:value={newKeyInput}
									placeholder="sk-..."
									class="w-full retro-input rounded"
								/>
								<a href="https://platform.openai.com/api-keys" target="_blank" class="text-xs font-mono text-blue-400 hover:text-blue-300 mt-1 inline-block">
									# get key at platform.openai.com/api-keys
								</a>
							</div>
							{#if newKeyError}
								<p class="text-sm font-mono text-red-400">{newKeyError}</p>
							{/if}
							{#if newKeyModels.length === 0}
								<RetroButton
									onclick={validateNewKey}
									disabled={newKeyValidating || !newKeyInput.trim()}
									variant="primary"
									class="w-full"
								>
									{newKeyValidating ? 'validating...' : 'validate key'}
								</RetroButton>
							{:else}
								<div class="space-y-3 pt-2 border-t border-surface-700">
									<label for="new-model" class="block text-xs font-mono text-surface-500 uppercase tracking-wider">Model</label>
									<select id="new-model" bind:value={newKeySelectedModel} class="w-full retro-input rounded">
										{#each newKeyModels as model}
											<option value={model}>{model}</option>
										{/each}
									</select>
									<RetroButton
										onclick={saveNewKey}
										disabled={saving}
										variant="primary"
										class="w-full"
									>
										{saving ? 'saving...' : 'save & continue'}
									</RetroButton>
								</div>
							{/if}
						</div>
					</RetroCard>
				</div>

			{:else}
				<!-- MAIN SETTINGS -->

			<!-- OpenAI Configuration -->
			<RetroCard variant="glow-blue" noPadding>
				<div class="px-4 py-2 border-b retro-border bg-blue-900/10 flex items-center justify-between">
					<div class="flex items-center gap-2">
						<span class="font-mono text-surface-100">OpenAI</span>
						<span class="text-xs px-1.5 py-0.5 bg-blue-600 text-white rounded font-mono">active</span>
							{#if openaiSource}
								<span class="text-xs px-1.5 py-0.5 rounded font-mono {openaiSource === 'env' ? 'bg-amber-900/30 text-amber-400' : 'bg-surface-700 text-surface-400'}">
									{openaiSource === 'env' ? 'env' : 'saved'}
								</span>
							{/if}
						</div>
						<RetroButton size="sm" onclick={startUpdateKey}>
							update key
						</RetroButton>
					</div>
					<div class="p-4">
						<label for="active-model" class="block text-xs font-mono text-surface-500 mb-1 uppercase tracking-wider">Model</label>
						<div class="flex gap-2">
							<select
								id="active-model"
								bind:value={openaiSelectedModel}
								class="flex-1 retro-input rounded"
							>
								{#each openaiModels as model}
									<option value={model}>{model}</option>
								{/each}
							</select>
							<RetroButton variant="primary" onclick={updateModel} disabled={saving}>
								{saving ? '...' : 'update'}
							</RetroButton>
						</div>
					</div>
				</RetroCard>

				<!-- Embeddings -->
				<RetroCard noPadding>
					<div class="px-4 py-2 border-b retro-border flex items-center gap-2">
						<span class="text-purple-400 font-mono text-xs">$</span>
						<span class="font-mono text-sm text-surface-300">embeddings</span>
					</div>
					<div class="p-4 space-y-4">
						<div class="grid grid-cols-2 gap-4">
							<div>
								<label for="embed-provider" class="block text-xs font-mono text-surface-500 mb-1 uppercase tracking-wider">Provider</label>
								<select id="embed-provider" bind:value={embeddingProvider} class="w-full retro-input rounded">
									{#each EMBEDDING_PROVIDERS as ep}
										<option value={ep.value}>{ep.label}</option>
									{/each}
								</select>
							</div>
							<div>
								<label for="embed-model" class="block text-xs font-mono text-surface-500 mb-1 uppercase tracking-wider">Model</label>
								<select id="embed-model" bind:value={embeddingModel} class="w-full retro-input rounded">
									{#each EMBEDDING_MODELS[embeddingProvider] || [] as em}
										<option value={em}>{em}</option>
									{/each}
								</select>
							</div>
						</div>

						{#if embeddingProvider === 'fastembed'}
							<div>
								<label for="hf-token" class="block text-xs font-mono text-surface-500 mb-1 uppercase tracking-wider">
									HuggingFace Token
									{#if hasHuggingFaceToken}
										<span class="text-emerald-400 ml-1">[configured]</span>
									{/if}
								</label>
								<input
									id="hf-token"
									type="password"
									bind:value={huggingFaceToken}
									placeholder={hasHuggingFaceToken ? '(leave empty to keep current)' : 'hf_...'}
									class="w-full retro-input rounded"
								/>
								<p class="text-xs font-mono text-surface-600 mt-1"># optional, for private models</p>
							</div>
						{/if}

						<div class="flex justify-end">
							<RetroButton variant="primary" onclick={saveEmbeddingSettings} disabled={saving}>
								{saving ? 'saving...' : 'save embeddings'}
							</RetroButton>
						</div>
					</div>
				</RetroCard>

				<!-- Web Search (Exa) -->
				<RetroCard noPadding>
					<div class="px-4 py-2 border-b retro-border flex items-center gap-2">
						<span class="text-blue-400 font-mono text-xs">@</span>
						<span class="font-mono text-sm text-surface-300">web search (Exa)</span>
						{#if hasExaApiKey}
							<span class="text-xs px-1.5 py-0.5 bg-emerald-900/30 text-emerald-400 rounded font-mono ml-auto">configured</span>
						{/if}
					</div>
					<div class="p-4 space-y-4">
						<div class="flex items-center gap-3">
							<input
								type="checkbox"
								id="web-search-enabled"
								bind:checked={webSearchEnabled}
								class="w-4 h-4 rounded border-surface-600 bg-surface-900 text-emerald-500 focus:ring-emerald-500"
							/>
							<label for="web-search-enabled" class="text-sm font-mono text-surface-300">
								Enable web search for real-time information
							</label>
						</div>

						<div>
							<label for="exa-key" class="block text-xs font-mono text-surface-500 mb-1 uppercase tracking-wider">
								Exa API Key
								{#if hasExaApiKey}
									<span class="text-emerald-400 ml-1">[configured]</span>
								{/if}
							</label>
							<input
								id="exa-key"
								type="password"
								bind:value={exaApiKey}
								placeholder={hasExaApiKey ? '(leave empty to keep current)' : 'exa-...'}
								class="w-full retro-input rounded"
							/>
							<a href="https://dashboard.exa.ai/api-keys" target="_blank" class="text-xs font-mono text-blue-400 hover:text-blue-300 mt-1 inline-block">
								# get key at dashboard.exa.ai/api-keys
							</a>
						</div>

						<div class="flex justify-end">
							<RetroButton variant="primary" onclick={saveExaSettings} disabled={saving}>
								{saving ? 'saving...' : 'save web search'}
							</RetroButton>
						</div>
					</div>
				</RetroCard>

				<!-- Reranking (Cohere) -->
				<RetroCard noPadding>
					<div class="px-4 py-2 border-b retro-border flex items-center gap-2">
						<span class="text-amber-400 font-mono text-xs">#</span>
						<span class="font-mono text-sm text-surface-300">reranking (Cohere)</span>
						{#if hasCohereApiKey}
							<span class="text-xs px-1.5 py-0.5 bg-emerald-900/30 text-emerald-400 rounded font-mono ml-auto">configured</span>
						{/if}
					</div>
					<div class="p-4 space-y-4">
						<p class="text-sm font-mono text-surface-500">
							Cohere reranking improves retrieval quality by reordering search results.
						</p>

						<div>
							<label for="cohere-key" class="block text-xs font-mono text-surface-500 mb-1 uppercase tracking-wider">
								Cohere API Key
								{#if hasCohereApiKey}
									<span class="text-emerald-400 ml-1">[configured]</span>
								{/if}
							</label>
							<input
								id="cohere-key"
								type="password"
								bind:value={cohereApiKey}
								placeholder={hasCohereApiKey ? '(leave empty to keep current)' : 'your-cohere-key'}
								class="w-full retro-input rounded"
							/>
							<a href="https://dashboard.cohere.com/api-keys" target="_blank" class="text-xs font-mono text-blue-400 hover:text-blue-300 mt-1 inline-block">
								# get key at dashboard.cohere.com/api-keys
							</a>
						</div>

						<div class="flex justify-end">
							<RetroButton variant="primary" onclick={saveCohereSettings} disabled={saving || !cohereApiKey.trim()}>
								{saving ? 'saving...' : 'save cohere key'}
							</RetroButton>
						</div>
					</div>
				</RetroCard>

				<!-- Tips -->
				<div class="text-xs font-mono text-surface-600 space-y-1">
					<p># keys can be set via env vars (OPENAI_API_KEY, EXA_API_KEY, COHERE_API_KEY)</p>
					<p># without Cohere, reranking falls back to a local cross-encoder model</p>
				</div>
			{/if}
		</div>
	</div>

	<!-- Add/Update Key Modal -->
	{#if showAddKey && !isOnboarding}
		<div class="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
			<RetroCard noPadding class="w-full max-w-md">
				<div class="px-4 py-3 border-b retro-border flex items-center justify-between">
					<div class="flex items-center gap-2">
						<span class="font-mono text-surface-100">
							{isUpdatingKey ? 'Update OpenAI Key' : 'Add OpenAI Key'}
						</span>
					</div>
					<RetroButton size="sm" onclick={cancelAddKey}>x</RetroButton>
				</div>

				<div class="p-4 space-y-4">
					<div>
						<label for="modal-api-key" class="block text-xs font-mono text-surface-500 mb-1 uppercase tracking-wider">API Key</label>
						<input
							id="modal-api-key"
							type="password"
							bind:value={newKeyInput}
							placeholder="sk-..."
							class="w-full retro-input rounded"
						/>
						<a href="https://platform.openai.com/api-keys" target="_blank" class="text-xs font-mono text-blue-400 hover:text-blue-300 mt-1 inline-block">
							get key
						</a>
						{#if isUpdatingKey && openaiSource === 'env'}
							<p class="text-xs font-mono text-amber-400 mt-2"># will override the environment variable key</p>
						{/if}
					</div>
					{#if newKeyError}
						<p class="text-sm font-mono text-red-400">{newKeyError}</p>
					{/if}
					{#if newKeyModels.length === 0}
						<RetroButton
							onclick={validateNewKey}
							disabled={newKeyValidating || !newKeyInput.trim()}
							class="w-full"
						>
							{newKeyValidating ? 'validating...' : 'validate'}
						</RetroButton>
					{:else}
						<div class="space-y-3 pt-2 border-t border-surface-700">
							<label for="modal-new-model" class="block text-xs font-mono text-surface-500 uppercase tracking-wider">Model</label>
							<select id="modal-new-model" bind:value={newKeySelectedModel} class="w-full retro-input rounded">
								{#each newKeyModels as model}
									<option value={model}>{model}</option>
								{/each}
							</select>
							<RetroButton
								variant="primary"
								class="w-full"
								onclick={saveNewKey}
								disabled={saving}
							>
								{saving ? 'saving...' : isUpdatingKey ? 'update key' : 'save key'}
							</RetroButton>
						</div>
					{/if}
				</div>
			</RetroCard>
		</div>
	{/if}
</div>
