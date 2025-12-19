<script lang="ts">
	import { onMount } from 'svelte';
	import {
		getSettings,
		updateSettings,
		validateApiKey,
		getClusters,
		getClusterInfo,
		connectCluster,
		disconnectCluster,
		type Settings,
		type KafkaCluster,
		type ClusterInfo
	} from '$lib/api';
	import { completeOnboarding } from '$lib/stores/onboarding.svelte';
	import { Header, HeaderStatus, IconButton, Card, Icon } from '$lib/components';
	import { LoadingState, StatusMessage } from '$lib/components/common';
	import { Hint } from '$lib/components/hints';
	import {
		OpenAISection,
		KafkaSection,
		EmbeddingsSection,
		WebSearchSection,
		RerankingSection
	} from '$lib/components/settings/sections';

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
	let openaiApiKey = $state('');
	let openaiValidationError = $state<string | null>(null);

	// Embedding settings
	let embeddingProvider = $state('fastembed');
	let embeddingModel = $state('BAAI/bge-small-en-v1.5');

	// Exa web search settings
	let exaApiKey = $state('');
	let hasExaApiKey = $state(false);

	// Cohere reranking settings
	let cohereApiKey = $state('');
	let hasCohereApiKey = $state(false);

	// Onboarding
	let isOnboarding = $state(false);

	// Kafka cluster state
	let clusters = $state<KafkaCluster[]>([]);
	let clusterInfo = $state<Partial<ClusterInfo> & { connected: boolean }>({ connected: false });
	let clusterLoading = $state(false);
	let clusterConnecting = $state(false);
	let clusterError = $state<string | null>(null);
	let showClusterForm = $state(false);
	let clusterFormName = $state('');
	let clusterFormBootstrap = $state('');
	let clusterFormProtocol = $state('PLAINTEXT');

	// ===== API Functions =====

	async function loadSettings() {
		loading = true;
		error = null;
		try {
			settings = await getSettings();
			openaiSelectedModel = settings.llm_model || '';
			embeddingProvider = settings.embedding_provider || 'fastembed';
			embeddingModel = settings.embedding_model || 'BAAI/bge-small-en-v1.5';
			hasCohereApiKey = settings.has_cohere_key || false;
			hasExaApiKey = settings.has_exa_key || false;

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
		try {
			const result = await validateApiKey('openai', '__USE_STORED__');
			openaiValid = result.valid;
			openaiModels = result.models;
			if (result.models.length > 0) {
				openaiSelectedModel = result.models.includes(openaiSelectedModel)
					? openaiSelectedModel
					: result.models[0];
			}
		} catch {
			openaiValid = false;
		} finally {
			openaiValidating = false;
		}
	}

	async function saveOpenAISettings() {
		saving = true;
		openaiValidationError = null;
		try {
			if (openaiApiKey.trim()) {
				openaiValidating = true;
				const result = await validateApiKey('openai', openaiApiKey.trim());
				openaiValidating = false;

				if (!result.valid) {
					openaiValidationError = result.message || 'Invalid API key';
					saving = false;
					return;
				}

				openaiModels = result.models;
				if (!result.models.includes(openaiSelectedModel)) {
					openaiSelectedModel = result.models[0] || '';
				}

				await updateSettings({
					llm_provider: 'openai',
					llm_model: openaiSelectedModel,
					openai_api_key: openaiApiKey.trim()
				});

				openaiConfigured = true;
				openaiSource = 'db';
				openaiValid = true;
				openaiApiKey = '';
				isOnboarding = false;
				completeOnboarding();
			} else {
				await updateSettings({ llm_model: openaiSelectedModel });
			}
			showSuccess('OpenAI settings saved');
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed';
		} finally {
			saving = false;
			openaiValidating = false;
		}
	}

	async function saveEmbeddingSettings() {
		saving = true;
		try {
			await updateSettings({
				embedding_provider: embeddingProvider,
				embedding_model: embeddingModel
			});
			showSuccess('Embedding settings saved');
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed';
		} finally {
			saving = false;
		}
	}

	async function saveExaSettings() {
		saving = true;
		try {
			if (exaApiKey.trim()) {
				await updateSettings({ exa_api_key: exaApiKey.trim() });
				hasExaApiKey = true;
				exaApiKey = '';
				showSuccess('Web search settings saved');
			}
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
				showSuccess('Cohere API key saved');
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed';
		} finally {
			saving = false;
		}
	}

	// Kafka cluster functions
	async function loadClusterData() {
		clusterLoading = true;
		clusterError = null;
		try {
			const [clustersResult, infoResult] = await Promise.all([
				getClusters().catch(() => []),
				getClusterInfo().catch(() => ({ connected: false }))
			]);
			clusters = clustersResult;
			clusterInfo = infoResult;
		} catch (e) {
			clusterError = e instanceof Error ? e.message : 'Failed to load cluster data';
		} finally {
			clusterLoading = false;
		}
	}

	async function handleClusterConnect(cluster?: KafkaCluster) {
		clusterConnecting = true;
		clusterError = null;
		try {
			if (cluster) {
				await connectCluster({
					name: cluster.name,
					bootstrap_servers: cluster.bootstrap_servers,
					security_protocol: cluster.security_protocol
				});
			} else {
				await connectCluster({
					name: clusterFormName,
					bootstrap_servers: clusterFormBootstrap,
					security_protocol: clusterFormProtocol
				});
				showClusterForm = false;
				clusterFormName = '';
				clusterFormBootstrap = '';
				clusterFormProtocol = 'PLAINTEXT';
			}
			await loadClusterData();
			showSuccess('Connected to cluster');
		} catch (e) {
			clusterError = e instanceof Error ? e.message : 'Failed to connect';
		} finally {
			clusterConnecting = false;
		}
	}

	async function handleClusterDisconnect() {
		try {
			await disconnectCluster();
			await loadClusterData();
			showSuccess('Disconnected from cluster');
		} catch (e) {
			clusterError = e instanceof Error ? e.message : 'Failed to disconnect';
		}
	}

	function connectDemoCluster() {
		clusterFormName = 'Demo Cluster';
		clusterFormBootstrap = 'localhost:9094';
		clusterFormProtocol = 'PLAINTEXT';
		showClusterForm = true;
	}

	function showSuccess(message: string) {
		success = message;
		setTimeout(() => { success = null; }, 2000);
	}

	onMount(() => {
		loadSettings();
		loadClusterData();
	});
</script>

<svelte:head>
	<title>Settings - kGPT</title>
</svelte:head>

<div class="flex flex-col h-full bg-bg">
	<Header title="Settings" subtitle="Configure your kGPT instance">
		{#snippet actions()}
			{#if openaiValid && openaiSelectedModel && !isOnboarding}
				<HeaderStatus
					status="active"
					label="Active"
					sublabel="openai/{openaiSelectedModel}"
					pulse
				/>
			{/if}
		{/snippet}
	</Header>

	<div class="flex-1 overflow-y-auto p-6">
		<div class="max-w-3xl mx-auto space-y-4">
			<!-- Messages -->
			{#if error}
				<StatusMessage variant="error" message={error}>
					{#snippet actions()}
						<IconButton
							variant="danger"
							size="sm"
							title="Dismiss error"
							onclick={() => error = null}
						>
							<Icon name="x" size="sm" />
						</IconButton>
					{/snippet}
				</StatusMessage>
			{/if}
			{#if success}
				<StatusMessage variant="success" message={success} />
			{/if}

			{#if loading}
				<div class="flex items-center justify-center py-16">
					<div class="text-center">
						<LoadingState
							message="Loading settings..."
							showSpinner={true}
							size="xl"
							class="flex-col gap-4 text-text-secondary [&>svg]:text-primary"
						/>
					</div>
				</div>

			{:else if isOnboarding && !openaiValid}
				<!-- ONBOARDING -->
				<div class="space-y-4">
					<div class="text-center py-8">
						<h2 class="text-2xl font-semibold text-text mb-2">Welcome to kGPT</h2>
						<p class="text-text-secondary text-sm">Configure your OpenAI API key to get started</p>
					</div>

					<OpenAISection
						source={openaiSource}
						models={openaiModels}
						selectedModel={openaiSelectedModel}
						apiKey={openaiApiKey}
						hasApiKey={openaiConfigured}
						{saving}
						validating={openaiValidating}
						validationError={openaiValidationError}
						onsave={saveOpenAISettings}
						onmodelchange={(v) => openaiSelectedModel = v}
						onapikeychange={(v) => openaiApiKey = v}
					/>
				</div>

			{:else}
				<!-- MAIN SETTINGS -->

				<OpenAISection
					source={openaiSource}
					models={openaiModels}
					selectedModel={openaiSelectedModel}
					apiKey={openaiApiKey}
					hasApiKey={openaiConfigured}
					{saving}
					validating={openaiValidating}
					validationError={openaiValidationError}
					onsave={saveOpenAISettings}
					onmodelchange={(v) => openaiSelectedModel = v}
					onapikeychange={(v) => openaiApiKey = v}
				/>

				<KafkaSection
					{clusterInfo}
					{clusters}
					loading={clusterLoading}
					connecting={clusterConnecting}
					error={clusterError}
					showForm={showClusterForm}
					formName={clusterFormName}
					formBootstrap={clusterFormBootstrap}
					formProtocol={clusterFormProtocol}
					onconnect={handleClusterConnect}
					ondisconnect={handleClusterDisconnect}
					onconnectdemo={connectDemoCluster}
					onshowform={() => showClusterForm = true}
					onhideform={() => showClusterForm = false}
					onformnamechange={(v) => clusterFormName = v}
					onformbootstrapchange={(v) => clusterFormBootstrap = v}
					onformprotocolchange={(v) => clusterFormProtocol = v}
				/>

				<EmbeddingsSection
					provider={embeddingProvider}
					model={embeddingModel}
					{saving}
					onsave={saveEmbeddingSettings}
					onproviderchange={(v) => embeddingProvider = v}
					onmodelchange={(v) => embeddingModel = v}
				/>

				<WebSearchSection
					apiKey={exaApiKey}
					hasApiKey={hasExaApiKey}
					{saving}
					onsave={saveExaSettings}
					onapikeychange={(v) => exaApiKey = v}
				/>

				<RerankingSection
					apiKey={cohereApiKey}
					hasApiKey={hasCohereApiKey}
					{saving}
					onsave={saveCohereSettings}
					onapikeychange={(v) => cohereApiKey = v}
				/>

				<!-- Tips -->
				<div class="text-xs text-text-tertiary space-y-1 pt-2">
					<p>Keys can also be set via environment variables (OPENAI_API_KEY, EXA_API_KEY, COHERE_API_KEY)</p>
					<p>Without Cohere, reranking falls back to a local cross-encoder model</p>
				</div>
			{/if}
		</div>
	</div>

	<Hint
		id="settings"
		title="Configure Your Setup"
		description="Customize AI providers, connect Kafka clusters, and fine-tune your kGPT experience here."
	/>
</div>
