<script lang="ts">
	import { onMount } from 'svelte';
	import {
		getSettings,
		updateSettings,
		validateApiKey,
		type Settings,
		type KeyStatus
	} from '$lib/api';

	let settings = $state<Settings | null>(null);
	let loading = $state(true);
	let saving = $state(false);
	let error = $state<string | null>(null);
	let success = $state<string | null>(null);

	// Current active configuration
	let activeProvider = $state('');
	let activeModel = $state('');

	// Provider state
	interface ProviderConfig {
		configured: boolean;
		source: 'env' | 'db' | null;
		validating: boolean;
		valid: boolean;
		models: string[];
		selectedModel: string;
		error: string | null;
	}

	let providerConfigs = $state<Record<string, ProviderConfig>>({
		openai: { configured: false, source: null, validating: false, valid: false, models: [], selectedModel: '', error: null },
		anthropic: { configured: false, source: null, validating: false, valid: false, models: [], selectedModel: '', error: null },
		openrouter: { configured: false, source: null, validating: false, valid: false, models: [], selectedModel: '', error: null },
		ollama: { configured: false, source: null, validating: false, valid: false, models: [], selectedModel: '', error: null }
	});

	// For adding/updating keys
	let showAddKey = $state<string | null>(null);
	let isUpdatingKey = $state(false);
	let newKeyInput = $state('');
	let newKeyValidating = $state(false);
	let newKeyError = $state<string | null>(null);
	let newKeyModels = $state<string[]>([]);
	let newKeySelectedModel = $state('');

	// Ollama host
	let ollamaHost = $state('http://ollama:11434');

	// Embedding settings
	let embeddingProvider = $state('fastembed');
	let embeddingModel = $state('BAAI/bge-small-en-v1.5');
	let huggingFaceToken = $state('');
	let hasHuggingFaceToken = $state(false);

	// Onboarding
	let isOnboarding = $state(false);
	let onboardingStep = $state(1);

	const PROVIDERS: Record<string, { name: string; keyPrefix: string; docsUrl: string }> = {
		openai: { name: 'OpenAI', keyPrefix: 'sk-', docsUrl: 'https://platform.openai.com/api-keys' },
		anthropic: { name: 'Anthropic', keyPrefix: 'sk-ant-', docsUrl: 'https://console.anthropic.com/settings/keys' },
		openrouter: { name: 'OpenRouter', keyPrefix: 'sk-or-', docsUrl: 'https://openrouter.ai/keys' },
		ollama: { name: 'Ollama', keyPrefix: '', docsUrl: 'https://ollama.ai' }
	};

	const EMBEDDING_PROVIDERS = [
		{ value: 'fastembed', label: 'FastEmbed (Local)' },
		{ value: 'openai', label: 'OpenAI' },
		{ value: 'ollama', label: 'Ollama' }
	];

	const EMBEDDING_MODELS: Record<string, string[]> = {
		fastembed: ['BAAI/bge-small-en-v1.5', 'BAAI/bge-base-en-v1.5', 'snowflake/arctic-embed-m'],
		openai: ['text-embedding-3-small', 'text-embedding-3-large'],
		ollama: ['nomic-embed-text', 'mxbai-embed-large']
	};

	const hasAnyProvider = $derived(
		Object.values(providerConfigs).some(p => p.configured && p.valid)
	);

	async function loadSettings() {
		loading = true;
		error = null;

		try {
			settings = await getSettings();
			activeProvider = settings.llm_provider || '';
			activeModel = settings.llm_model || '';
			ollamaHost = settings.ollama_host || 'http://ollama:11434';
			embeddingProvider = settings.embedding_provider || 'fastembed';
			embeddingModel = settings.embedding_model || 'BAAI/bge-small-en-v1.5';
			hasHuggingFaceToken = settings.has_huggingface_token || false;

			// Check which providers are configured
			const configuredProviders: string[] = [];

			if (settings.openai_key?.configured) {
				providerConfigs = { ...providerConfigs, openai: { ...providerConfigs.openai, configured: true, source: settings.openai_key.source } };
				configuredProviders.push('openai');
			}
			if (settings.anthropic_key?.configured) {
				providerConfigs = { ...providerConfigs, anthropic: { ...providerConfigs.anthropic, configured: true, source: settings.anthropic_key.source } };
				configuredProviders.push('anthropic');
			}
			if (settings.openrouter_key?.configured) {
				providerConfigs = { ...providerConfigs, openrouter: { ...providerConfigs.openrouter, configured: true, source: settings.openrouter_key.source } };
				configuredProviders.push('openrouter');
			}

			providerConfigs = { ...providerConfigs, ollama: { ...providerConfigs.ollama, configured: true, source: null } };

			// Validate all configured providers
			await Promise.all(configuredProviders.map(p => validateProvider(p)));
			await validateProvider('ollama');

			if (!activeProvider || !providerConfigs[activeProvider]?.valid) {
				const validProvider = Object.entries(providerConfigs).find(([_, c]) => c.valid);
				if (!validProvider) {
					isOnboarding = true;
				}
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load settings';
		} finally {
			loading = false;
		}
	}

	async function validateProvider(provider: string) {
		providerConfigs = { ...providerConfigs, [provider]: { ...providerConfigs[provider], validating: true, error: null } };

		try {
			const result =
				provider === 'ollama'
					? await validateApiKey(provider, '__USE_STORED__', { ollama_host: ollamaHost })
					: await validateApiKey(provider, '__USE_STORED__');
			providerConfigs = {
				...providerConfigs,
				[provider]: {
					...providerConfigs[provider],
					validating: false,
					valid: result.valid,
					models: result.models,
					selectedModel: result.models.includes(activeModel) ? activeModel : (result.models[0] || ''),
					error: result.valid ? null : result.message
				}
			};
		} catch (e) {
			providerConfigs = {
				...providerConfigs,
				[provider]: { ...providerConfigs[provider], validating: false, valid: false, error: e instanceof Error ? e.message : 'Failed' }
			};
		}
	}

	async function switchToProvider(provider: string) {
		const config = providerConfigs[provider];
		if (!config.valid || !config.selectedModel) return;

		saving = true;
		try {
			const updates: Partial<Settings> = { llm_provider: provider, llm_model: config.selectedModel };
			if (provider === 'ollama') updates.ollama_host = ollamaHost;
			await updateSettings(updates);
			activeProvider = provider;
			activeModel = config.selectedModel;
			success = `Switched to ${PROVIDERS[provider].name}`;
			setTimeout(() => { success = null; }, 2000);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed';
		} finally {
			saving = false;
		}
	}

	async function updateModel() {
		const config = providerConfigs[activeProvider];
		if (!config || config.selectedModel === activeModel) return;

		saving = true;
		try {
			await updateSettings({ llm_model: config.selectedModel });
			activeModel = config.selectedModel;
			success = 'Model updated';
			setTimeout(() => { success = null; }, 2000);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed';
		} finally {
			saving = false;
		}
	}

	async function validateNewKey() {
		if (!showAddKey || !newKeyInput.trim()) return;
		newKeyValidating = true;
		newKeyError = null;

		try {
			const result =
				showAddKey === 'ollama'
					? await validateApiKey(showAddKey, newKeyInput.trim(), { ollama_host: ollamaHost })
					: await validateApiKey(showAddKey, newKeyInput.trim());
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
		if (!showAddKey || !newKeyInput.trim() || !newKeySelectedModel) return;
		saving = true;

		try {
			const updates: Partial<Settings> = { llm_provider: showAddKey, llm_model: newKeySelectedModel };
			if (showAddKey === 'openai') updates.openai_api_key = newKeyInput.trim();
			if (showAddKey === 'anthropic') updates.anthropic_api_key = newKeyInput.trim();
			if (showAddKey === 'openrouter') updates.openrouter_api_key = newKeyInput.trim();

			await updateSettings(updates);
			providerConfigs = {
				...providerConfigs,
				[showAddKey]: { configured: true, source: 'db', validating: false, valid: true, models: newKeyModels, selectedModel: newKeySelectedModel, error: null }
			};
			activeProvider = showAddKey;
			activeModel = newKeySelectedModel;
			success = `${PROVIDERS[showAddKey].name} configured!`;
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
		showAddKey = null;
		isUpdatingKey = false;
		newKeyInput = '';
		newKeyError = null;
		newKeyModels = [];
		newKeySelectedModel = '';
	}

	function startUpdateKey(provider: string) {
		showAddKey = provider;
		isUpdatingKey = true;
		newKeyInput = '';
		newKeyError = null;
		newKeyModels = [];
		newKeySelectedModel = '';
	}

	async function saveEmbeddingSettings() {
		saving = true;
		try {
			const updates: Partial<Settings> = { embedding_provider: embeddingProvider, embedding_model: embeddingModel };
			if (huggingFaceToken.trim()) updates.huggingface_token = huggingFaceToken.trim();
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

	function selectModel(provider: string, model: string) {
		providerConfigs = { ...providerConfigs, [provider]: { ...providerConfigs[provider], selectedModel: model } };
	}

	onMount(() => { loadSettings(); });
</script>

<div class="flex flex-col h-full bg-surface-900">
	<!-- Header -->
	<header class="px-6 py-4 border-b border-surface-700 bg-surface-800/50">
		<div class="flex items-center justify-between">
			<div class="flex items-center gap-3">
				<span class="text-emerald-400 font-mono text-sm">$</span>
				<h1 class="font-mono text-lg text-surface-100">kgpt/settings</h1>
				<span class="text-surface-500 font-mono text-sm">--configure</span>
			</div>
			{#if activeProvider && activeModel && !isOnboarding}
				<div class="px-3 py-1 bg-surface-800 border border-surface-700 rounded font-mono text-sm">
					<span class="text-surface-500">active:</span>
					<span class="text-emerald-400 ml-1">{activeProvider}/{activeModel}</span>
				</div>
			{/if}
		</div>
	</header>

	<div class="flex-1 overflow-y-auto p-6">
		<div class="max-w-3xl mx-auto space-y-6">
			<!-- Messages -->
			{#if error}
				<div class="bg-red-900/20 border border-red-800 rounded p-3 font-mono text-sm text-red-400">
					<span class="text-red-500">error:</span> {error}
				</div>
			{/if}
			{#if success}
				<div class="bg-emerald-900/20 border border-emerald-800 rounded p-3 font-mono text-sm text-emerald-400">
					<span class="text-emerald-500">✓</span> {success}
				</div>
			{/if}

			{#if loading}
				<div class="bg-surface-800 border border-surface-700 rounded p-8 text-center font-mono text-surface-500 animate-pulse">
					loading...
				</div>

			{:else if isOnboarding && !hasAnyProvider}
				<!-- ONBOARDING -->
				<div class="space-y-6">
					<div class="text-center py-6">
						<h2 class="text-xl font-mono text-surface-100 mb-2">Welcome to kGPT</h2>
						<p class="text-surface-500 font-mono text-sm">Configure an LLM provider to get started</p>
					</div>

					{#if !showAddKey}
						<div class="space-y-2">
							{#each Object.entries(PROVIDERS) as [key, provider]}
								<button
									onclick={() => { showAddKey = key; onboardingStep = 2; }}
									class="w-full flex items-center gap-4 p-4 bg-surface-800 hover:bg-surface-700 border border-surface-700 hover:border-surface-600 rounded transition-all text-left font-mono"
								>
									<div class="flex-1">
										<div class="text-surface-100">{provider.name}</div>
										<div class="text-xs text-surface-500">
											{key === 'ollama' ? 'Local models, no API key' : 'Requires API key'}
										</div>
									</div>
									<span class="text-surface-600">→</span>
								</button>
							{/each}
						</div>
					{:else}
						{@const provider = PROVIDERS[showAddKey]}
						<div class="bg-surface-800 border border-surface-700 rounded">
							<div class="px-4 py-2 border-b border-surface-700 flex items-center gap-2">
								<button onclick={cancelAddKey} class="text-surface-500 hover:text-surface-300 font-mono text-sm">← back</button>
								<span class="text-surface-600">|</span>
								<span class="font-mono text-surface-100">{provider.name}</span>
							</div>

							<div class="p-4 space-y-4">
								{#if showAddKey === 'ollama'}
									<div>
										<label for="ollama-host" class="block text-xs font-mono text-surface-500 mb-1">--host</label>
										<input id="ollama-host" type="text" bind:value={ollamaHost} placeholder="http://localhost:11434"
											class="w-full px-3 py-2 bg-surface-900 border border-surface-600 rounded font-mono text-sm text-surface-100 focus:outline-none focus:border-emerald-500" />
									</div>
									<button onclick={() => validateProvider('ollama')} disabled={providerConfigs.ollama.validating}
										class="w-full py-2 bg-surface-700 hover:bg-surface-600 text-surface-100 rounded font-mono text-sm transition-colors disabled:opacity-50">
										{providerConfigs.ollama.validating ? 'testing...' : 'test connection'}
									</button>
									{#if providerConfigs.ollama.valid && providerConfigs.ollama.models.length > 0}
										<div class="space-y-2">
											<label for="ollama-model" class="block text-xs font-mono text-surface-500">--model</label>
											<select id="ollama-model" bind:value={providerConfigs.ollama.selectedModel}
												class="w-full px-3 py-2 bg-surface-900 border border-surface-600 rounded font-mono text-sm text-surface-100">
												{#each providerConfigs.ollama.models as model}
													<option value={model}>{model}</option>
												{/each}
											</select>
											<button onclick={() => { switchToProvider('ollama'); isOnboarding = false; }} disabled={saving}
												class="w-full py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded font-mono text-sm">
												{saving ? 'saving...' : 'use ollama →'}
											</button>
										</div>
									{:else if providerConfigs.ollama.error}
										<p class="text-sm font-mono text-red-400">{providerConfigs.ollama.error}</p>
									{/if}
								{:else}
									<div>
										<label for="api-key" class="block text-xs font-mono text-surface-500 mb-1">--api-key</label>
										<input id="api-key" type="password" bind:value={newKeyInput} placeholder={provider.keyPrefix + '...'}
											class="w-full px-3 py-2 bg-surface-900 border border-surface-600 rounded font-mono text-sm text-surface-100 focus:outline-none focus:border-emerald-500" />
										<a href={provider.docsUrl} target="_blank" class="text-xs font-mono text-blue-400 hover:text-blue-300 mt-1 inline-block">
											# get key at {provider.docsUrl.replace('https://', '')}
										</a>
									</div>
									{#if newKeyError}
										<p class="text-sm font-mono text-red-400">{newKeyError}</p>
									{/if}
									{#if newKeyModels.length === 0}
										<button onclick={validateNewKey} disabled={newKeyValidating || !newKeyInput.trim()}
											class="w-full py-2 bg-surface-700 hover:bg-surface-600 text-surface-100 rounded font-mono text-sm disabled:opacity-50">
											{newKeyValidating ? 'validating...' : 'validate key'}
										</button>
									{:else}
										<div class="space-y-2 pt-2 border-t border-surface-700">
											<label for="new-model" class="block text-xs font-mono text-surface-500">--model</label>
											<select id="new-model" bind:value={newKeySelectedModel}
												class="w-full px-3 py-2 bg-surface-900 border border-surface-600 rounded font-mono text-sm text-surface-100">
												{#each newKeyModels as model}
													<option value={model}>{model}</option>
												{/each}
											</select>
											<button onclick={saveNewKey} disabled={saving}
												class="w-full py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded font-mono text-sm">
												{saving ? 'saving...' : `use ${provider.name.toLowerCase()} →`}
											</button>
										</div>
									{/if}
								{/if}
							</div>
						</div>
					{/if}
				</div>

			{:else}
				<!-- MAIN SETTINGS -->

				<!-- Active Provider -->
				{#if activeProvider && providerConfigs[activeProvider]?.valid}
					{@const config = providerConfigs[activeProvider]}
					<section class="bg-surface-800 border border-emerald-700/50 rounded">
						<div class="px-4 py-2 border-b border-emerald-700/30 bg-emerald-900/10 flex items-center justify-between">
							<div class="flex items-center gap-2">
								<span class="font-mono text-surface-100">{PROVIDERS[activeProvider].name}</span>
								<span class="text-xs px-1.5 py-0.5 bg-emerald-600 text-white rounded font-mono">active</span>
								{#if config.source}
									<span class="text-xs px-1.5 py-0.5 rounded font-mono {config.source === 'env' ? 'bg-amber-900/30 text-amber-400' : 'bg-surface-700 text-surface-400'}">
										{config.source === 'env' ? 'env' : 'saved'}
									</span>
								{/if}
							</div>
							{#if activeProvider !== 'ollama'}
								<button onclick={() => startUpdateKey(activeProvider)}
									class="px-2 py-1 text-xs font-mono text-surface-400 hover:text-surface-200 hover:bg-surface-700 rounded transition-colors">
									update key
								</button>
							{/if}
						</div>
						<div class="p-4">
							<label for="active-model" class="block text-xs font-mono text-surface-500 mb-1">--model</label>
							<div class="flex gap-2">
								<select id="active-model" value={config.selectedModel} onchange={(e) => selectModel(activeProvider, e.currentTarget.value)}
									class="flex-1 px-3 py-2 bg-surface-900 border border-surface-600 rounded font-mono text-sm text-surface-100 focus:outline-none focus:border-emerald-500">
									{#each config.models as model}
										<option value={model}>{model}</option>
									{/each}
								</select>
								{#if config.selectedModel !== activeModel}
									<button onclick={updateModel} disabled={saving}
										class="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded font-mono text-sm">
										{saving ? '...' : 'update'}
									</button>
								{/if}
							</div>
						</div>
					</section>
				{/if}

				<!-- Other Providers -->
				<section class="bg-surface-800 border border-surface-700 rounded">
					<div class="px-4 py-2 border-b border-surface-700 flex items-center gap-2">
						<span class="text-blue-400 font-mono text-xs">></span>
						<span class="font-mono text-sm text-surface-300">switch --provider</span>
					</div>
					<div class="divide-y divide-surface-700">
						{#each Object.entries(PROVIDERS) as [key, provider]}
							{#if key !== activeProvider}
								{@const config = providerConfigs[key]}
								<div class="p-4 flex items-center justify-between">
									<div class="flex items-center gap-3">
										<span class="font-mono text-surface-100">{provider.name}</span>
										{#if config.configured && config.source}
											<span class="text-xs px-1.5 py-0.5 rounded font-mono {config.source === 'env' ? 'bg-amber-900/30 text-amber-400' : 'bg-surface-700 text-surface-400'}">
												{config.source === 'env' ? 'env' : 'saved'}
											</span>
										{/if}
										{#if config.validating}
											<span class="text-xs font-mono text-surface-500 animate-pulse">checking...</span>
										{/if}
									</div>

									<div class="flex items-center gap-2">
										{#if config.valid && config.models.length > 0}
											<select bind:value={config.selectedModel}
												class="px-2 py-1 bg-surface-900 border border-surface-600 rounded font-mono text-xs text-surface-100">
												{#each config.models as model}
													<option value={model}>{model}</option>
												{/each}
											</select>
											<button onclick={() => switchToProvider(key)} disabled={saving}
												class="px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded font-mono text-xs">
												switch
											</button>
											{#if key !== 'ollama'}
												<button onclick={() => startUpdateKey(key)}
													class="px-2 py-1 text-xs font-mono text-surface-500 hover:text-surface-300 hover:bg-surface-700 rounded transition-colors">
													update
												</button>
											{/if}
										{:else if config.configured && !config.valid && !config.validating}
											<span class="text-xs font-mono text-red-400">{config.error || 'error'}</span>
											<button onclick={() => validateProvider(key)}
												class="px-3 py-1 bg-surface-700 hover:bg-surface-600 text-surface-300 rounded font-mono text-xs">
												retry
											</button>
											{#if key !== 'ollama'}
												<button onclick={() => startUpdateKey(key)}
													class="px-2 py-1 text-xs font-mono text-surface-500 hover:text-surface-300 hover:bg-surface-700 rounded transition-colors">
													update
												</button>
											{/if}
										{:else if !config.configured}
											<button onclick={() => { showAddKey = key; }}
												class="px-3 py-1 bg-surface-700 hover:bg-surface-600 text-surface-300 rounded font-mono text-xs">
												add key
											</button>
										{/if}
									</div>
								</div>
							{/if}
						{/each}
					</div>
				</section>

				<!-- Embeddings -->
				<section class="bg-surface-800 border border-surface-700 rounded">
					<div class="px-4 py-2 border-b border-surface-700 flex items-center gap-2">
						<span class="text-purple-400 font-mono text-xs">⚡</span>
						<span class="font-mono text-sm text-surface-300">embeddings</span>
					</div>
					<div class="p-4 space-y-4">
						<div class="grid grid-cols-2 gap-4">
							<div>
								<label for="embed-provider" class="block text-xs font-mono text-surface-500 mb-1">--provider</label>
								<select id="embed-provider" bind:value={embeddingProvider}
									class="w-full px-3 py-2 bg-surface-900 border border-surface-600 rounded font-mono text-sm text-surface-100 focus:outline-none focus:border-emerald-500">
									{#each EMBEDDING_PROVIDERS as ep}
										<option value={ep.value}>{ep.label}</option>
									{/each}
								</select>
							</div>
							<div>
								<label for="embed-model" class="block text-xs font-mono text-surface-500 mb-1">--model</label>
								<select id="embed-model" bind:value={embeddingModel}
									class="w-full px-3 py-2 bg-surface-900 border border-surface-600 rounded font-mono text-sm text-surface-100 focus:outline-none focus:border-emerald-500">
									{#each EMBEDDING_MODELS[embeddingProvider] || [] as em}
										<option value={em}>{em}</option>
									{/each}
								</select>
							</div>
						</div>

						{#if embeddingProvider === 'fastembed'}
							<div>
								<label for="hf-token" class="block text-xs font-mono text-surface-500 mb-1">
									--huggingface-token
									{#if hasHuggingFaceToken}
										<span class="text-emerald-400 ml-1">✓ set</span>
									{/if}
								</label>
								<input id="hf-token" type="password" bind:value={huggingFaceToken}
									placeholder={hasHuggingFaceToken ? '••••••••  (leave empty to keep)' : 'hf_...'}
									class="w-full px-3 py-2 bg-surface-900 border border-surface-600 rounded font-mono text-sm text-surface-100 placeholder-surface-600 focus:outline-none focus:border-emerald-500" />
								<p class="text-xs font-mono text-surface-600 mt-1"># get at huggingface.co/settings/tokens</p>
							</div>
						{/if}

						<div class="flex justify-end">
							<button onclick={saveEmbeddingSettings} disabled={saving}
								class="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:bg-surface-700 disabled:text-surface-500 text-white font-mono text-sm rounded transition-colors">
								{saving ? 'saving...' : 'save embeddings'}
							</button>
						</div>
					</div>
				</section>

				<!-- Tips -->
				<section class="text-xs font-mono text-surface-600 space-y-1">
					<p># keys can be set via env vars (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)</p>
					<p># for ollama in docker, use host: http://ollama:11434</p>
				</section>
			{/if}
		</div>
	</div>

	<!-- Add/Update Key Modal -->
	{#if showAddKey && !isOnboarding}
		{@const provider = PROVIDERS[showAddKey]}
		<div class="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
			<div class="bg-surface-800 border border-surface-700 rounded w-full max-w-md">
				<div class="px-4 py-3 border-b border-surface-700 flex items-center justify-between">
					<div class="flex items-center gap-2">
						<span class="font-mono text-surface-100">
							{showAddKey === 'ollama' ? 'Configure Ollama' : isUpdatingKey ? `Update ${provider.name} Key` : `Add ${provider.name} Key`}
						</span>
					</div>
					<button onclick={cancelAddKey} class="text-surface-500 hover:text-surface-300 text-xl leading-none">&times;</button>
				</div>

				<div class="p-4 space-y-4">
					{#if showAddKey === 'ollama'}
						<div>
							<label for="modal-ollama-host" class="block text-xs font-mono text-surface-500 mb-1">--host</label>
							<input id="modal-ollama-host" type="text" bind:value={ollamaHost} placeholder="http://localhost:11434"
								class="w-full px-3 py-2 bg-surface-900 border border-surface-600 rounded font-mono text-sm text-surface-100 focus:outline-none focus:border-emerald-500" />
						</div>
						<button onclick={() => validateProvider('ollama')} disabled={providerConfigs.ollama.validating}
							class="w-full py-2 bg-surface-700 hover:bg-surface-600 text-surface-100 rounded font-mono text-sm">
							{providerConfigs.ollama.validating ? 'testing...' : 'test connection'}
						</button>
						{#if providerConfigs.ollama.valid && providerConfigs.ollama.models.length > 0}
							<select bind:value={providerConfigs.ollama.selectedModel}
								class="w-full px-3 py-2 bg-surface-900 border border-surface-600 rounded font-mono text-sm text-surface-100">
								{#each providerConfigs.ollama.models as model}
									<option value={model}>{model}</option>
								{/each}
							</select>
							<button onclick={() => { switchToProvider('ollama'); cancelAddKey(); }}
								class="w-full py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded font-mono text-sm">
								switch to ollama
							</button>
						{:else if providerConfigs.ollama.error}
							<p class="text-sm font-mono text-red-400">{providerConfigs.ollama.error}</p>
						{/if}
					{:else}
						<div>
							<label for="modal-api-key" class="block text-xs font-mono text-surface-500 mb-1">--api-key</label>
							<input id="modal-api-key" type="password" bind:value={newKeyInput} placeholder={provider.keyPrefix + '...'}
								class="w-full px-3 py-2 bg-surface-900 border border-surface-600 rounded font-mono text-sm text-surface-100 focus:outline-none focus:border-emerald-500" />
							<a href={provider.docsUrl} target="_blank" class="text-xs font-mono text-blue-400 hover:text-blue-300 mt-1 inline-block">get key →</a>
							{#if isUpdatingKey && providerConfigs[showAddKey]?.source === 'env'}
								<p class="text-xs font-mono text-amber-400 mt-2"># will override the environment variable key</p>
							{/if}
						</div>
						{#if newKeyError}
							<p class="text-sm font-mono text-red-400">{newKeyError}</p>
						{/if}
						{#if newKeyModels.length === 0}
							<button onclick={validateNewKey} disabled={newKeyValidating || !newKeyInput.trim()}
								class="w-full py-2 bg-surface-700 hover:bg-surface-600 text-surface-100 rounded font-mono text-sm disabled:opacity-50">
								{newKeyValidating ? 'validating...' : 'validate'}
							</button>
						{:else}
							<div class="space-y-3 pt-2 border-t border-surface-700">
								<label for="modal-new-model" class="block text-xs font-mono text-surface-500">--model</label>
								<select id="modal-new-model" bind:value={newKeySelectedModel}
									class="w-full px-3 py-2 bg-surface-900 border border-surface-600 rounded font-mono text-sm text-surface-100">
									{#each newKeyModels as model}
										<option value={model}>{model}</option>
									{/each}
								</select>
								<button onclick={saveNewKey} disabled={saving}
									class="w-full py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded font-mono text-sm">
									{saving ? 'saving...' : isUpdatingKey ? 'update & switch' : 'save & switch'}
								</button>
							</div>
						{/if}
					{/if}
				</div>
			</div>
		</div>
	{/if}
</div>
