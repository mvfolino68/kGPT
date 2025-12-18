<script lang="ts">
	import { onMount } from 'svelte';
	import { getSettings, updateSettings, getAvailableModels, type Settings } from '$lib/api';

	let settings = $state<Settings | null>(null);
	let loading = $state(true);
	let saving = $state(false);
	let error = $state<string | null>(null);
	let success = $state<string | null>(null);

	// Available models per provider
	let availableModels = $state<string[]>([]);
	let loadingModels = $state(false);

	// Form state (editable copies)
	let formProvider = $state('openai');
	let formModel = $state('');
	let formEmbeddingProvider = $state('fastembed');
	let formEmbeddingModel = $state('BAAI/bge-small-en-v1.5');
	let formOpenAIKey = $state('');
	let formAnthropicKey = $state('');
	let formOpenRouterKey = $state('');
	let formHuggingFaceToken = $state('');
	let formOllamaHost = $state('http://ollama:11434');

	const LLM_PROVIDERS = [
		{ value: 'openai', label: 'OpenAI', requiresKey: 'openai_api_key' },
		{ value: 'anthropic', label: 'Anthropic', requiresKey: 'anthropic_api_key' },
		{ value: 'openrouter', label: 'OpenRouter', requiresKey: 'openrouter_api_key' },
		{ value: 'ollama', label: 'Ollama (Local)', requiresKey: null }
	];

	const EMBEDDING_PROVIDERS = [
		{ value: 'fastembed', label: 'FastEmbed (Local)' },
		{ value: 'openai', label: 'OpenAI' },
		{ value: 'ollama', label: 'Ollama' },
		{ value: 'cohere', label: 'Cohere' }
	];

	const DEFAULT_MODELS: Record<string, string[]> = {
		openai: ['gpt-4o', 'gpt-4o-mini', 'o3-mini', 'o1-preview'],
		anthropic: ['claude-3-7-sonnet-20250219', 'claude-3-5-sonnet-latest', 'claude-3-5-haiku-latest'],
		openrouter: ['anthropic/claude-3.7-sonnet', 'google/gemini-2.0-flash-001', 'deepseek/deepseek-chat', 'openai/gpt-4o-mini'],
		ollama: ['llama3.3', 'llama3.2', 'mistral-small', 'deepseek-r1:14b']
	};

	const EMBEDDING_MODELS: Record<string, string[]> = {
		fastembed: ['BAAI/bge-small-en-v1.5', 'BAAI/bge-base-en-v1.5', 'snowflake/arctic-embed-m'],
		openai: ['text-embedding-3-small', 'text-embedding-3-large', 'text-embedding-ada-002'],
		ollama: ['nomic-embed-text', 'mxbai-embed-large'],
		cohere: ['embed-english-v3.0', 'embed-multilingual-v3.0']
	};

	async function loadSettings() {
		loading = true;
		error = null;
		try {
			settings = await getSettings();
			// Populate form with current settings
			formProvider = settings.llm_provider || 'openai';
			formModel = settings.llm_model || '';
			formEmbeddingProvider = settings.embedding_provider || 'fastembed';
			formEmbeddingModel = settings.embedding_model || 'BAAI/bge-small-en-v1.5';
			formOpenAIKey = settings.openai_api_key || '';
			formAnthropicKey = settings.anthropic_api_key || '';
			formOpenRouterKey = settings.openrouter_api_key || '';
			formOllamaHost = settings.ollama_host || 'http://ollama:11434';

			// Load models for current provider
			await loadModels(formProvider);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load settings';
		} finally {
			loading = false;
		}
	}

	async function loadModels(provider: string) {
		loadingModels = true;
		try {
			availableModels = await getAvailableModels(provider);
		} catch {
			// Fall back to default models
			availableModels = DEFAULT_MODELS[provider] || [];
		} finally {
			loadingModels = false;
		}
	}

	async function handleProviderChange() {
		await loadModels(formProvider);
		// Set a default model for the new provider
		if (availableModels.length > 0 && !availableModels.includes(formModel)) {
			formModel = availableModels[0];
		}
	}

	async function handleSave() {
		saving = true;
		error = null;
		success = null;

		try {
			const updates: Partial<Settings> = {
				llm_provider: formProvider,
				llm_model: formModel,
				embedding_provider: formEmbeddingProvider,
				embedding_model: formEmbeddingModel,
				ollama_host: formOllamaHost
			};

			// Only include API keys if they're set
			if (formOpenAIKey) updates.openai_api_key = formOpenAIKey;
			if (formAnthropicKey) updates.anthropic_api_key = formAnthropicKey;
			if (formOpenRouterKey) updates.openrouter_api_key = formOpenRouterKey;
			if (formHuggingFaceToken) updates.huggingface_token = formHuggingFaceToken;

			settings = await updateSettings(updates);
			success = 'Settings saved successfully!';

			// Clear success message after 3 seconds
			setTimeout(() => { success = null; }, 3000);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to save settings';
		} finally {
			saving = false;
		}
	}

	onMount(() => {
		loadSettings();
	});
</script>

<div class="flex flex-col h-full bg-surface-900">
	<!-- Terminal-style header -->
	<header class="px-6 py-4 border-b border-surface-700 bg-surface-800/50">
		<div class="flex items-center gap-3">
			<span class="text-emerald-400 font-mono text-sm">$</span>
			<h1 class="font-mono text-lg text-surface-100">kgpt/settings</h1>
			<span class="text-surface-500 font-mono text-sm">--configure</span>
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
				<div class="bg-surface-800 border border-surface-700 rounded p-8 text-center font-mono text-surface-500">
					<span class="animate-pulse">loading...</span>
				</div>
			{:else}
				<!-- LLM Provider Section -->
				<section class="bg-surface-800 border border-surface-700 rounded">
					<div class="px-4 py-2 border-b border-surface-700 flex items-center gap-2">
						<span class="text-blue-400 font-mono text-xs">&gt;</span>
						<span class="font-mono text-sm text-surface-300">llm --provider</span>
					</div>

					<div class="p-4 space-y-4">
						<div class="grid grid-cols-2 gap-4">
							<div>
								<label class="block text-xs font-mono text-surface-500 mb-1">--provider</label>
								<select
									bind:value={formProvider}
									onchange={handleProviderChange}
									class="w-full px-2 py-1.5 bg-surface-900 border border-surface-600 rounded font-mono text-sm text-surface-100 focus:outline-none focus:border-emerald-500"
								>
									{#each LLM_PROVIDERS as provider}
										<option value={provider.value}>{provider.label}</option>
									{/each}
								</select>
							</div>

							<div>
								<label class="block text-xs font-mono text-surface-500 mb-1">
									--model
									{#if loadingModels}
										<span class="text-surface-600 ml-1">loading...</span>
									{/if}
								</label>
								<select
									bind:value={formModel}
									class="w-full px-2 py-1.5 bg-surface-900 border border-surface-600 rounded font-mono text-sm text-surface-100 focus:outline-none focus:border-emerald-500"
								>
									{#each availableModels as model}
										<option value={model}>{model}</option>
									{/each}
								</select>
							</div>
						</div>
					</div>
				</section>

				<!-- API Keys Section -->
				<section class="bg-surface-800 border border-surface-700 rounded">
					<div class="px-4 py-2 border-b border-surface-700 flex items-center gap-2">
						<span class="text-amber-400 font-mono text-xs">🔑</span>
						<span class="font-mono text-sm text-surface-300">api-keys</span>
					</div>

					<div class="p-4 space-y-4">
						<!-- OpenAI -->
						<div class:opacity-50={formProvider !== 'openai' && formEmbeddingProvider !== 'openai'}>
							<label class="block text-xs font-mono text-surface-500 mb-1">
								--openai-key
								{#if formProvider === 'openai'}
									<span class="text-emerald-400 ml-1">(active)</span>
								{/if}
							</label>
							<input
								type="password"
								bind:value={formOpenAIKey}
								placeholder="sk-..."
								class="w-full px-2 py-1.5 bg-surface-900 border border-surface-600 rounded font-mono text-sm text-surface-100 placeholder-surface-600 focus:outline-none focus:border-emerald-500"
							/>
						</div>

						<!-- Anthropic -->
						<div class:opacity-50={formProvider !== 'anthropic'}>
							<label class="block text-xs font-mono text-surface-500 mb-1">
								--anthropic-key
								{#if formProvider === 'anthropic'}
									<span class="text-emerald-400 ml-1">(active)</span>
								{/if}
							</label>
							<input
								type="password"
								bind:value={formAnthropicKey}
								placeholder="sk-ant-..."
								class="w-full px-2 py-1.5 bg-surface-900 border border-surface-600 rounded font-mono text-sm text-surface-100 placeholder-surface-600 focus:outline-none focus:border-emerald-500"
							/>
						</div>

						<!-- OpenRouter -->
						<div class:opacity-50={formProvider !== 'openrouter'}>
							<label class="block text-xs font-mono text-surface-500 mb-1">
								--openrouter-key
								{#if formProvider === 'openrouter'}
									<span class="text-emerald-400 ml-1">(active)</span>
								{/if}
							</label>
							<input
								type="password"
								bind:value={formOpenRouterKey}
								placeholder="sk-or-..."
								class="w-full px-2 py-1.5 bg-surface-900 border border-surface-600 rounded font-mono text-sm text-surface-100 placeholder-surface-600 focus:outline-none focus:border-emerald-500"
							/>
						</div>

						<!-- Ollama Host -->
						<div class:opacity-50={formProvider !== 'ollama'}>
							<label class="block text-xs font-mono text-surface-500 mb-1">
								--ollama-host
								{#if formProvider === 'ollama'}
									<span class="text-emerald-400 ml-1">(active)</span>
								{/if}
							</label>
							<input
								type="text"
								bind:value={formOllamaHost}
								placeholder="http://localhost:11434"
								class="w-full px-2 py-1.5 bg-surface-900 border border-surface-600 rounded font-mono text-sm text-surface-100 placeholder-surface-600 focus:outline-none focus:border-emerald-500"
							/>
							<p class="text-xs text-surface-600 font-mono mt-1">
								# use http://ollama:11434 in docker
							</p>
						</div>
					</div>
				</section>

				<!-- Embeddings Section -->
				<section class="bg-surface-800 border border-surface-700 rounded">
					<div class="px-4 py-2 border-b border-surface-700 flex items-center gap-2">
						<span class="text-purple-400 font-mono text-xs">⚡</span>
						<span class="font-mono text-sm text-surface-300">embeddings</span>
					</div>

					<div class="p-4 space-y-4">
						<div class="grid grid-cols-2 gap-4">
							<div>
								<label class="block text-xs font-mono text-surface-500 mb-1">--provider</label>
								<select
									bind:value={formEmbeddingProvider}
									class="w-full px-2 py-1.5 bg-surface-900 border border-surface-600 rounded font-mono text-sm text-surface-100 focus:outline-none focus:border-emerald-500"
								>
									{#each EMBEDDING_PROVIDERS as provider}
										<option value={provider.value}>{provider.label}</option>
									{/each}
								</select>
							</div>

							<div>
								<label class="block text-xs font-mono text-surface-500 mb-1">--model</label>
								<select
									bind:value={formEmbeddingModel}
									class="w-full px-2 py-1.5 bg-surface-900 border border-surface-600 rounded font-mono text-sm text-surface-100 focus:outline-none focus:border-emerald-500"
								>
									{#each EMBEDDING_MODELS[formEmbeddingProvider] || [] as model}
										<option value={model}>{model}</option>
									{/each}
								</select>
							</div>
						</div>

						<!-- Hugging Face Token -->
						<div class:opacity-50={formEmbeddingProvider !== 'fastembed'}>
							<label class="block text-xs font-mono text-surface-500 mb-1">
								--huggingface-token
								{#if formEmbeddingProvider === 'fastembed'}
									<span class="text-amber-400 ml-1">(required for model download)</span>
								{/if}
								{#if settings?.has_huggingface_token}
									<span class="text-emerald-400 ml-1">✓ set</span>
								{/if}
							</label>
							<input
								type="password"
								bind:value={formHuggingFaceToken}
								placeholder="hf_..."
								class="w-full px-2 py-1.5 bg-surface-900 border border-surface-600 rounded font-mono text-sm text-surface-100 placeholder-surface-600 focus:outline-none focus:border-emerald-500"
							/>
							<p class="text-xs text-surface-600 font-mono mt-1">
								# get at huggingface.co/settings/tokens
							</p>
						</div>
					</div>
				</section>

				<!-- Save Button -->
				<div class="flex justify-end">
					<button
						type="button"
						onclick={handleSave}
						disabled={saving}
						class="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:bg-surface-700 disabled:text-surface-500 text-white font-mono text-sm rounded transition-colors"
					>
						{saving ? 'saving...' : 'save'}
					</button>
				</div>
			{/if}
		</div>
	</div>
</div>
