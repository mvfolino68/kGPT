<script lang="ts">
	import { onMount } from 'svelte';
	import {
		getSettings,
		updateSettings,
		validateApiKey,
		type Settings,
		type KeyStatus
	} from '$lib/api';
	import { Header, StatusIndicator } from '$lib/components';

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
			success = 'OpenAI API key saved';
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

<svelte:head>
	<title>Settings - kGPT</title>
</svelte:head>

<div class="flex flex-col h-full bg-surface-900">
	<Header title="Settings" subtitle="Configure your kGPT instance">
		{#snippet actions()}
			{#if openaiValid && openaiSelectedModel && !isOnboarding}
				<div class="px-3 py-1.5 bg-surface-800 rounded border border-surface-700/50 text-xs flex items-center gap-2">
					<StatusIndicator status="active" size="sm" pulse />
					<span class="text-surface-500">active:</span>
					<span class="text-primary-light">openai/{openaiSelectedModel}</span>
				</div>
			{/if}
		{/snippet}
	</Header>

	<div class="flex-1 overflow-y-auto p-6">
		<div class="max-w-4xl mx-auto space-y-4">
			<!-- Messages -->
			{#if error}
				<div class="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-sm text-red-400 flex items-center gap-2">
					<StatusIndicator status="error" size="sm" />
					<span>{error}</span>
				</div>
			{/if}
			{#if success}
				<div class="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-3 text-sm text-emerald-400 flex items-center gap-2">
					<StatusIndicator status="active" size="sm" />
					<span>{success}</span>
				</div>
			{/if}

			{#if loading}
				<div class="bg-surface-900 border border-surface-700/50 rounded-lg p-8 text-center text-surface-500 flex items-center justify-center gap-2">
					<StatusIndicator status="warning" pulse />
					Loading...
				</div>

			{:else if isOnboarding && !openaiValid}
				<!-- ONBOARDING -->
				<div class="space-y-4">
					<div class="bg-surface-900 border border-primary/30 rounded-lg text-center py-6">
						<h2 class="text-2xl font-bold text-primary-light mb-2">Welcome to kGPT</h2>
						<p class="text-surface-400 text-sm">Configure your OpenAI API key to get started</p>
					</div>

					<div class="bg-surface-900 border border-surface-700/50 rounded-lg p-4 space-y-4">
						<div>
							<label for="api-key" class="block text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-1.5">OpenAI API Key</label>
							<input
								id="api-key"
								type="password"
								bind:value={newKeyInput}
								placeholder="sk-..."
								class="w-full input"
							/>
							<a href="https://platform.openai.com/api-keys" target="_blank" class="text-xs text-primary-light hover:underline mt-1 inline-block">
								Get key at platform.openai.com/api-keys
							</a>
						</div>
						{#if newKeyError}
							<p class="text-sm text-red-400">{newKeyError}</p>
						{/if}
						{#if newKeyModels.length === 0}
							<button
								type="button"
								onclick={validateNewKey}
								disabled={newKeyValidating || !newKeyInput.trim()}
								class="btn btn-primary w-full"
							>
								{newKeyValidating ? 'Validating...' : 'Validate Key'}
							</button>
						{:else}
							<div class="space-y-3 pt-2 border-t border-surface-700/50">
								<label for="new-model" class="block text-[10px] font-bold uppercase tracking-wider text-surface-500">Model</label>
								<select id="new-model" bind:value={newKeySelectedModel} class="w-full input">
									{#each newKeyModels as model}
										<option value={model}>{model}</option>
									{/each}
								</select>
								<button
									type="button"
									onclick={saveNewKey}
									disabled={saving}
									class="btn btn-primary w-full"
								>
									{saving ? 'Saving...' : 'Save & Continue'}
								</button>
							</div>
						{/if}
					</div>
				</div>

			{:else}
				<!-- MAIN SETTINGS -->

				<!-- OpenAI Configuration -->
				<div class="bg-surface-900 border border-primary/30 rounded-lg overflow-hidden">
					<div class="px-4 py-3 border-b border-surface-700/50 bg-primary/5 flex items-center justify-between">
						<div class="flex items-center gap-2">
							<span class="font-medium text-surface-100">OpenAI</span>
							<span class="text-xs px-1.5 py-0.5 bg-primary text-white rounded">active</span>
							{#if openaiSource}
								<span class="text-xs px-1.5 py-0.5 rounded {openaiSource === 'env' ? 'bg-amber-500/20 text-amber-400' : 'bg-surface-700 text-surface-400'}">
									{openaiSource === 'env' ? 'env' : 'saved'}
								</span>
							{/if}
						</div>
						<button type="button" class="btn btn-ghost btn-sm" onclick={startUpdateKey}>
							Update Key
						</button>
					</div>
					<div class="p-4">
						<label for="active-model" class="block text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-1.5">Model</label>
						<div class="flex gap-2">
							<select id="active-model" bind:value={openaiSelectedModel} class="flex-1 input">
								{#each openaiModels as model}
									<option value={model}>{model}</option>
								{/each}
							</select>
							<button type="button" class="btn btn-primary" onclick={updateModel} disabled={saving}>
								{saving ? '...' : 'Update'}
							</button>
						</div>
					</div>
				</div>

				<!-- Embeddings -->
				<div class="bg-surface-900 border border-surface-700/50 rounded-lg overflow-hidden">
					<div class="px-4 py-3 border-b border-surface-700/50 flex items-center gap-2">
						<svg class="w-4 h-4 text-violet-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
						</svg>
						<span class="text-sm text-surface-300">Embeddings</span>
					</div>
					<div class="p-4 space-y-4">
						<div class="grid grid-cols-2 gap-4">
							<div>
								<label for="embed-provider" class="block text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-1.5">Provider</label>
								<select id="embed-provider" bind:value={embeddingProvider} class="w-full input">
									{#each EMBEDDING_PROVIDERS as ep}
										<option value={ep.value}>{ep.label}</option>
									{/each}
								</select>
							</div>
							<div>
								<label for="embed-model" class="block text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-1.5">Model</label>
								<select id="embed-model" bind:value={embeddingModel} class="w-full input">
									{#each EMBEDDING_MODELS[embeddingProvider] || [] as em}
										<option value={em}>{em}</option>
									{/each}
								</select>
							</div>
						</div>

						{#if embeddingProvider === 'fastembed'}
							<div>
								<label for="hf-token" class="block text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-1.5">
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
									class="w-full input"
								/>
								<p class="text-xs text-surface-500 mt-1">Optional, for private models</p>
							</div>
						{/if}

						<div class="flex justify-end">
							<button type="button" class="btn btn-primary" onclick={saveEmbeddingSettings} disabled={saving}>
								{saving ? 'Saving...' : 'Save Embeddings'}
							</button>
						</div>
					</div>
				</div>

				<!-- Web Search (Exa) -->
				<div class="bg-surface-900 border border-surface-700/50 rounded-lg overflow-hidden">
					<div class="px-4 py-3 border-b border-surface-700/50 flex items-center gap-2">
						<svg class="w-4 h-4 text-primary-light" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
						</svg>
						<span class="text-sm text-surface-300">Web Search (Exa)</span>
						{#if hasExaApiKey}
							<span class="text-xs px-1.5 py-0.5 bg-emerald-500/20 text-emerald-400 rounded ml-auto">configured</span>
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
							<label for="web-search-enabled" class="text-sm text-surface-300">
								Enable web search for real-time information
							</label>
						</div>

						<div>
							<label for="exa-key" class="block text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-1.5">
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
								class="w-full input"
							/>
							<a href="https://dashboard.exa.ai/api-keys" target="_blank" class="text-xs text-primary-light hover:underline mt-1 inline-block">
								Get key at dashboard.exa.ai/api-keys
							</a>
						</div>

						<div class="flex justify-end">
							<button type="button" class="btn btn-primary" onclick={saveExaSettings} disabled={saving}>
								{saving ? 'Saving...' : 'Save Web Search'}
							</button>
						</div>
					</div>
				</div>

				<!-- Reranking (Cohere) -->
				<div class="bg-surface-900 border border-surface-700/50 rounded-lg overflow-hidden">
					<div class="px-4 py-3 border-b border-surface-700/50 flex items-center gap-2">
						<svg class="w-4 h-4 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12" />
						</svg>
						<span class="text-sm text-surface-300">Reranking (Cohere)</span>
						{#if hasCohereApiKey}
							<span class="text-xs px-1.5 py-0.5 bg-emerald-500/20 text-emerald-400 rounded ml-auto">configured</span>
						{/if}
					</div>
					<div class="p-4 space-y-4">
						<p class="text-sm text-surface-500">
							Cohere reranking improves retrieval quality by reordering search results.
						</p>

						<div>
							<label for="cohere-key" class="block text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-1.5">
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
								class="w-full input"
							/>
							<a href="https://dashboard.cohere.com/api-keys" target="_blank" class="text-xs text-primary-light hover:underline mt-1 inline-block">
								Get key at dashboard.cohere.com/api-keys
							</a>
						</div>

						<div class="flex justify-end">
							<button type="button" class="btn btn-primary" onclick={saveCohereSettings} disabled={saving || !cohereApiKey.trim()}>
								{saving ? 'Saving...' : 'Save Cohere Key'}
							</button>
						</div>
					</div>
				</div>

				<!-- Tips -->
				<div class="text-xs text-surface-500 space-y-1">
					<p>Keys can also be set via environment variables (OPENAI_API_KEY, EXA_API_KEY, COHERE_API_KEY)</p>
					<p>Without Cohere, reranking falls back to a local cross-encoder model</p>
				</div>
			{/if}
		</div>
	</div>

	<!-- Add/Update Key Modal -->
	{#if showAddKey && !isOnboarding}
		<div class="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
			<div class="bg-surface-900 border border-surface-700/50 rounded-lg w-full max-w-md">
				<div class="px-4 py-3 border-b border-surface-700/50 flex items-center justify-between">
					<span class="font-medium text-surface-100">
						{isUpdatingKey ? 'Update OpenAI Key' : 'Add OpenAI Key'}
					</span>
					<button type="button" class="btn btn-ghost btn-sm" onclick={cancelAddKey}>x</button>
				</div>

				<div class="p-4 space-y-4">
					<div>
						<label for="modal-api-key" class="block text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-1.5">API Key</label>
						<input
							id="modal-api-key"
							type="password"
							bind:value={newKeyInput}
							placeholder="sk-..."
							class="w-full input"
						/>
						{#if isUpdatingKey && openaiSource === 'env'}
							<p class="text-xs text-amber-400 mt-2">This will override the environment variable key</p>
						{/if}
					</div>
					{#if newKeyError}
						<p class="text-sm text-red-400">{newKeyError}</p>
					{/if}
					{#if newKeyModels.length === 0}
						<button
							type="button"
							onclick={validateNewKey}
							disabled={newKeyValidating || !newKeyInput.trim()}
							class="btn btn-default w-full"
						>
							{newKeyValidating ? 'Validating...' : 'Validate'}
						</button>
					{:else}
						<div class="space-y-3 pt-2 border-t border-surface-700/50">
							<label for="modal-new-model" class="block text-[10px] font-bold uppercase tracking-wider text-surface-500">Model</label>
							<select id="modal-new-model" bind:value={newKeySelectedModel} class="w-full input">
								{#each newKeyModels as model}
									<option value={model}>{model}</option>
								{/each}
							</select>
							<button
								type="button"
								class="btn btn-primary w-full"
								onclick={saveNewKey}
								disabled={saving}
							>
								{saving ? 'Saving...' : isUpdatingKey ? 'Update Key' : 'Save Key'}
							</button>
						</div>
					{/if}
				</div>
			</div>
		</div>
	{/if}
</div>
