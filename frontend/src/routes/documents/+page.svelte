<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import {
		getDocuments,
		ingestDocument,
		deleteDocument,
		cancelIngestion,
		getIngestionStatus,
		getCollections,
		searchDocuments,
		browseVectors,
		getRAGPipelineInfo,
		runRAGDemo,
		generateEmbedding,
		compareEmbeddings,
		getSyncStatus,
		cleanupOrphanVectors,
		cleanupStaleEntries,
		purgeAllData,
		getChunkAnalytics,
		getAgentGraph,
		type DocumentSource,
		type CollectionsResponse,
		type VectorSearchResponse,
		type VectorBrowseResponse,
		type RAGPipelineInfo,
		type RAGDemoResponse,
		type ChunkResult,
		type SyncStatusResponse,
		type ChunkAnalytics,
		type AgentGraphInfo
	} from '$lib/api';
	import { RetroHeader, RetroButton, StatusIndicator, RetroCard } from '$lib/components';

	// =========================================================================
	// State
	// =========================================================================

	// Tab navigation
	type Tab = 'sources' | 'search' | 'browse' | 'pipeline' | 'agents';
	let activeTab = $state<Tab>('sources');

	// Sources tab state
	let documents = $state<DocumentSource[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);
	let ingesting = $state(false);

	// Sync state
	let syncStatus = $state<SyncStatusResponse | null>(null);
	let syncLoading = $state(false);
	let cleanupLoading = $state(false);

	// Form state
	let sourceType = $state<'sitemap' | 'github' | 'url'>('sitemap');
	let sourceName = $state('');
	let sourceUrl = $state('');

	// Delete confirmation state
	let confirmingDeleteId = $state<number | null>(null);

	// Destructive operation confirmation state
	type DestructiveOperation = 'cleanup_orphans' | 'cleanup_stale' | 'purge_all' | null;
	let activeDestructiveOp = $state<DestructiveOperation>(null);
	let destructiveConfirmText = $state('');
	let lastDestructiveResult = $state<{ type: DestructiveOperation; message: string } | null>(null);

	// Active ingestion tracking
	interface IngestionProgress {
		status: string;
		progress: number;
		stage: string;
		message: string;
		updated_at?: string;
		count?: number;
		pages?: number;
		pages_fetched?: number;
		pages_total?: number;
		pages_successful?: number;
		pages_processed?: number;
		documents_created?: number;
		chunks?: number;
		chunks_embedded?: number;
		error?: string;
		elapsed_seconds?: number;
	}
	let activeIngestions = $state<Map<number, IngestionProgress>>(new Map());
	let ingestionStartTimes = $state<Map<number, number>>(new Map());
	let pollInterval: ReturnType<typeof setInterval> | null = null;
	let timerInterval: ReturnType<typeof setInterval> | null = null;
	let currentTime = $state(Date.now());

	// Collections state
	let collections = $state<CollectionsResponse | null>(null);
	let collectionsLoading = $state(false);

	// Search tab state
	let searchQuery = $state('');
	let searchResults = $state<VectorSearchResponse | null>(null);
	let searchLoading = $state(false);
	let searchK = $state(10);
	let selectedSource = $state<string>('');

	// Browse tab state
	let browseResults = $state<VectorBrowseResponse | null>(null);
	let browseLoading = $state(false);
	let browseOffset = $state<string | null>(null);
	let browseHistory = $state<string[]>([]);
	let showVectors = $state(false);
	let selectedChunk = $state<ChunkResult | null>(null);

	// Pipeline tab state
	let pipelineInfo = $state<RAGPipelineInfo | null>(null);
	let pipelineLoading = $state(false);
	let demoQuery = $state('');
	let demoResult = $state<RAGDemoResponse | null>(null);
	let demoLoading = $state(false);

	// Agent Graph tab state
	let agentGraph = $state<AgentGraphInfo | null>(null);
	let agentGraphLoading = $state(false);

	// Embedding demo state
	let embedText1 = $state('');
	let embedText2 = $state('');
	let embedCompareResult = $state<{
		cosine_similarity: number;
		similarity_percent: number;
		interpretation: string;
	} | null>(null);
	let embedLoading = $state(false);

	// Analytics state
	let chunkAnalytics = $state<ChunkAnalytics | null>(null);
	let analyticsLoading = $state(false);

	// Preset sources
	const presetSources = [
		{ name: 'htmx', type: 'sitemap' as const, url: 'https://htmx.org/sitemap.xml', size: '~180' },
		{
			name: 'fastapi',
			type: 'sitemap' as const,
			url: 'https://fastapi.tiangolo.com/sitemap.xml',
			size: '~150'
		},
		{
			name: 'kafka',
			type: 'sitemap' as const,
			url: 'https://kafka.apache.org/sitemap.xml',
			size: '~500'
		},
		{
			name: 'confluent',
			type: 'sitemap' as const,
			url: 'https://docs.confluent.io/home/sitemap.xml',
			size: '5k+'
		}
	];

	// =========================================================================
	// Sources Tab Functions
	// =========================================================================

	async function loadDocuments() {
		loading = true;
		error = null;
		try {
			documents = await getDocuments();
			const indexingDocs = documents.filter((d) => d.status === 'indexing');
			if (indexingDocs.length > 0) {
				startPolling();
				for (const doc of indexingDocs) {
					if (!activeIngestions.has(doc.id)) {
						activeIngestions.set(doc.id, {
							status: 'running',
							progress: 0,
							stage: 'loading',
							message: 'Checking progress...'
						});
					}
					if (!ingestionStartTimes.has(doc.id)) {
						const startTime = doc.created_at ? new Date(doc.created_at).getTime() : Date.now();
						ingestionStartTimes.set(doc.id, startTime);
					}
				}
				activeIngestions = new Map(activeIngestions);
				ingestionStartTimes = new Map(ingestionStartTimes);
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load documents';
		} finally {
			loading = false;
		}
	}

	async function loadCollections() {
		collectionsLoading = true;
		try {
			collections = await getCollections();
		} catch (e) {
			console.error('Failed to load collections:', e);
		} finally {
			collectionsLoading = false;
		}
	}

	async function loadSyncStatus() {
		syncLoading = true;
		try {
			syncStatus = await getSyncStatus();
		} catch (e) {
			console.error('Failed to load sync status:', e);
		} finally {
			syncLoading = false;
		}
	}

	function startDestructiveOp(op: DestructiveOperation) {
		activeDestructiveOp = op;
		destructiveConfirmText = '';
		lastDestructiveResult = null;
	}

	function cancelDestructiveOp() {
		activeDestructiveOp = null;
		destructiveConfirmText = '';
	}

	async function handleCleanupOrphans() {
		if (destructiveConfirmText.toLowerCase() !== 'confirm delete') return;
		cleanupLoading = true;
		try {
			const result = await cleanupOrphanVectors();
			error = null;
			lastDestructiveResult = {
				type: 'cleanup_orphans',
				message: `Cleaned up ${result.orphans_found} orphan sources, ${result.total_vectors_deleted} vectors deleted`
			};
			await loadAll();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Cleanup failed';
		} finally {
			cleanupLoading = false;
			activeDestructiveOp = null;
			destructiveConfirmText = '';
		}
	}

	async function handleCleanupStale() {
		if (destructiveConfirmText.toLowerCase() !== 'confirm delete') return;
		cleanupLoading = true;
		try {
			const result = await cleanupStaleEntries();
			error = null;
			lastDestructiveResult = {
				type: 'cleanup_stale',
				message: `Cleaned up ${result.entries_cleaned} stale database entries`
			};
			await loadAll();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Cleanup failed';
		} finally {
			cleanupLoading = false;
			activeDestructiveOp = null;
			destructiveConfirmText = '';
		}
	}

	async function handlePurgeAll() {
		if (destructiveConfirmText.toLowerCase() !== 'confirm delete') return;
		cleanupLoading = true;
		try {
			const result = await purgeAllData();
			error = null;
			lastDestructiveResult = {
				type: 'purge_all',
				message: `Purged ${result.db_entries_deleted} sources and ${result.vectors_deleted} vectors`
			};
			await loadAll();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Purge failed';
		} finally {
			cleanupLoading = false;
			activeDestructiveOp = null;
			destructiveConfirmText = '';
		}
	}

	async function loadAll() {
		await Promise.all([loadDocuments(), loadCollections(), loadSyncStatus()]);
	}

	function startPolling() {
		if (pollInterval) return;
		pollInterval = setInterval(pollProgress, 1000);
		if (!timerInterval) {
			timerInterval = setInterval(() => {
				currentTime = Date.now();
			}, 1000);
		}
	}

	function stopPolling() {
		if (pollInterval) {
			clearInterval(pollInterval);
			pollInterval = null;
		}
		if (timerInterval) {
			clearInterval(timerInterval);
			timerInterval = null;
		}
	}

	function formatElapsedTime(startTime: number): string {
		const elapsed = Math.floor((currentTime - startTime) / 1000);
		const mins = Math.floor(elapsed / 60);
		const secs = elapsed % 60;
		return mins > 0 ? `${mins}m ${secs.toString().padStart(2, '0')}s` : `${secs}s`;
	}

	async function pollProgress() {
		const indexingIds = documents.filter((d) => d.status === 'indexing').map((d) => d.id);
		for (const [id] of activeIngestions) {
			if (!indexingIds.includes(id)) {
				const progress = activeIngestions.get(id);
				if (progress && progress.status === 'running') indexingIds.push(id);
			}
		}
		if (indexingIds.length === 0) {
			stopPolling();
			return;
		}

		for (const id of indexingIds) {
			try {
				const status = await getIngestionStatus(id);
				activeIngestions.set(id, status as IngestionProgress);
				if (
					status.status === 'completed' ||
					status.status === 'error' ||
					status.status === 'cancelled'
				) {
					await loadAll();
				}
			} catch (e) {
				console.error(`Failed to get status for ${id}:`, e);
			}
		}
		activeIngestions = new Map(activeIngestions);
	}

	async function handleIngest() {
		if (!sourceName.trim() || !sourceUrl.trim()) return;
		ingesting = true;
		error = null;
		try {
			const result = await ingestDocument({
				source_type: sourceType,
				name: sourceName,
				url: sourceUrl
			});
			activeIngestions.set(result.source_id, {
				status: 'running',
				progress: 0,
				stage: 'init',
				message: 'Starting...'
			});
			activeIngestions = new Map(activeIngestions);
			ingestionStartTimes.set(result.source_id, Date.now());
			ingestionStartTimes = new Map(ingestionStartTimes);
			startPolling();
			sourceName = '';
			sourceUrl = '';
			await loadDocuments();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to start ingestion';
		} finally {
			ingesting = false;
		}
	}

	async function handleCancel(id: number) {
		try {
			await cancelIngestion(id);
			const progress = activeIngestions.get(id);
			if (progress) {
				progress.status = 'cancelling';
				progress.message = 'Cancelling...';
				activeIngestions = new Map(activeIngestions);
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to cancel';
		}
	}

	function handleDeleteClick(id: number) {
		confirmingDeleteId = id;
	}

	function handleCancelDelete() {
		confirmingDeleteId = null;
	}

	async function handleConfirmDelete(id: number, _sourceName: string) {
		try {
			// Delete from database (backend also handles Qdrant cleanup)
			await deleteDocument(id);
			activeIngestions.delete(id);
			ingestionStartTimes.delete(id);
			activeIngestions = new Map(activeIngestions);
			ingestionStartTimes = new Map(ingestionStartTimes);
			await loadAll();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to delete';
		} finally {
			confirmingDeleteId = null;
		}
	}

	function selectPreset(preset: (typeof presetSources)[0]) {
		sourceType = preset.type;
		sourceName = preset.name;
		sourceUrl = preset.url;
	}

	function getStatusColor(status: string): string {
		// Returns the LED status type for StatusIndicator component
		const statusMap: Record<string, 'active' | 'warning' | 'error' | 'inactive'> = {
			indexed: 'active',
			indexing: 'warning',
			error: 'error',
			cancelled: 'inactive',
			pending: 'inactive'
		};
		return statusMap[status] || 'inactive';
	}

	function formatBytes(bytes: number): string {
		if (bytes === 0) return '—';
		const k = 1024;
		const sizes = ['B', 'KB', 'MB', 'GB'];
		const i = Math.floor(Math.log(bytes) / Math.log(k));
		return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
	}

	function estimateStorageSize(vectors: number, dims: number): string {
		// Rough estimate: vectors * dimensions * 4 bytes (float32) + ~500 bytes metadata per vector
		const vectorBytes = vectors * dims * 4;
		const metadataBytes = vectors * 500; // rough estimate for payload
		return formatBytes(vectorBytes + metadataBytes);
	}

	// =========================================================================
	// Search Tab Functions
	// =========================================================================

	async function handleSearch() {
		if (!searchQuery.trim()) return;
		searchLoading = true;
		try {
			searchResults = await searchDocuments(searchQuery, {
				k: searchK,
				source: selectedSource || undefined
			});
		} catch (e) {
			error = e instanceof Error ? e.message : 'Search failed';
		} finally {
			searchLoading = false;
		}
	}

	function getSimilarityColor(percent: number): string {
		if (percent >= 80) return 'text-emerald-400';
		if (percent >= 60) return 'text-lime-400';
		if (percent >= 40) return 'text-amber-400';
		return 'text-red-400';
	}

	// =========================================================================
	// Browse Tab Functions
	// =========================================================================

	async function loadVectors(offset?: string) {
		browseLoading = true;
		try {
			browseResults = await browseVectors({
				limit: 20,
				offset,
				withVectors: showVectors
			});
			if (offset) {
				browseHistory = [...browseHistory, offset];
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load vectors';
		} finally {
			browseLoading = false;
		}
	}

	function goBack() {
		if (browseHistory.length > 0) {
			browseHistory.pop();
			const prevOffset = browseHistory[browseHistory.length - 1] || undefined;
			loadVectors(prevOffset);
		}
	}

	// =========================================================================
	// Pipeline Tab Functions
	// =========================================================================

	async function loadPipelineInfo() {
		pipelineLoading = true;
		try {
			pipelineInfo = await getRAGPipelineInfo();
		} catch (e) {
			console.error('Failed to load pipeline info:', e);
		} finally {
			pipelineLoading = false;
		}
	}

	async function runDemo() {
		if (!demoQuery.trim()) return;
		demoLoading = true;
		try {
			demoResult = await runRAGDemo(demoQuery);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Demo failed';
		} finally {
			demoLoading = false;
		}
	}

	// =========================================================================
	// Agent Graph Tab Functions
	// =========================================================================

	async function loadAgentGraph() {
		agentGraphLoading = true;
		try {
			agentGraph = await getAgentGraph();
			console.log('Agent graph loaded:', agentGraph);
		} catch (e) {
			console.error('Failed to load agent graph:', e);
			error = e instanceof Error ? e.message : 'Failed to load agent graph';
		} finally {
			agentGraphLoading = false;
		}
	}

	async function handleEmbedCompare() {
		if (!embedText1.trim() || !embedText2.trim()) return;
		embedLoading = true;
		try {
			embedCompareResult = await compareEmbeddings(embedText1, embedText2);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Comparison failed';
		} finally {
			embedLoading = false;
		}
	}

	async function loadAnalytics() {
		analyticsLoading = true;
		try {
			chunkAnalytics = await getChunkAnalytics();
		} catch (e) {
			console.error('Failed to load analytics:', e);
		} finally {
			analyticsLoading = false;
		}
	}

	// =========================================================================
	// Lifecycle
	// =========================================================================

	onMount(() => {
		loadAll();
	});

	onDestroy(() => {
		stopPolling();
	});

	// Load tab-specific data when tab changes
	$effect(() => {
		if (activeTab === 'browse' && !browseResults) {
			loadVectors();
		}
		if (activeTab === 'pipeline' && !pipelineInfo) {
			loadPipelineInfo();
			loadAnalytics();
		}
		if (activeTab === 'agents' && !agentGraph) {
			loadAgentGraph();
		}
	});
</script>

<div class="flex flex-col h-full bg-surface-950">
	<!-- Retro Header with stats -->
	<RetroHeader path="kgpt/documents" flag="--vector-store">
		{#snippet rightContent()}
			<!-- Quick stats with LED indicators -->
			<div class="flex items-center gap-6 text-xs font-mono">
				{#if syncStatus}
					<div class="flex items-center gap-2">
						<StatusIndicator
							status={syncStatus.synced ? 'active' : 'warning'}
							size="sm"
							pulse={!syncStatus.synced}
						/>
						<span class="text-surface-500">sync:</span>
						<span class="{syncStatus.synced ? 'text-emerald-400' : 'text-amber-400'}">
							{syncStatus.synced ? 'OK' : 'WARN'}
						</span>
					</div>
				{/if}
				{#if collections}
					<div class="flex items-center gap-2 px-2 py-1 retro-card rounded">
						<span class="text-surface-500">col:</span>
						<span class="text-emerald-400">{collections.total_collections}</span>
					</div>
					<div class="flex items-center gap-2 px-2 py-1 retro-card rounded">
						<span class="text-surface-500">vec:</span>
						<span class="text-cyan-400">{collections.total_vectors.toLocaleString()}</span>
					</div>
				{/if}
				<div class="flex items-center gap-2 px-2 py-1 retro-card rounded">
					<span class="text-surface-500">src:</span>
					<span class="text-purple-400">{documents.length}</span>
				</div>
			</div>
		{/snippet}
	</RetroHeader>

	<!-- Tab navigation with retro style -->
	<nav class="px-6 border-b retro-border bg-surface-900/30 backdrop-blur-sm flex gap-1">
		{#each [
			{ id: 'sources' as Tab, label: 'Sources' },
			{ id: 'search' as Tab, label: 'Search' },
			{ id: 'browse' as Tab, label: 'Browse' },
			{ id: 'pipeline' as Tab, label: 'RAG Pipeline' },
			{ id: 'agents' as Tab, label: 'Agent Graph' }
		] as tab}
			<button
				onclick={() => (activeTab = tab.id)}
				class="px-4 py-2.5 font-mono text-sm transition-all {activeTab === tab.id
					? 'text-confluent-primary border-b-2 border-confluent-primary bg-surface-900/50'
					: 'text-surface-400 hover:text-surface-200 hover:bg-surface-800/30 border-b-2 border-transparent'}"
			>
				{activeTab === tab.id ? '> ' : ''}{tab.label}
			</button>
		{/each}
	</nav>

	<div class="flex-1 overflow-y-auto p-6">
		<div class="max-w-6xl mx-auto space-y-6">
			<!-- Error display -->
			{#if error}
				<div
					class="bg-red-900/20 border border-red-800 rounded p-3 font-mono text-sm text-red-400"
				>
					<span class="text-red-500">error:</span>
					{error}
					<button onclick={() => (error = null)} class="float-right text-red-500 hover:text-red-400"
						>×</button
					>
				</div>
			{/if}

			<!-- ================================================================= -->
			<!-- SOURCES TAB -->
			<!-- ================================================================= -->
			{#if activeTab === 'sources'}
				<!-- Ingest form -->
				<RetroCard noPadding>
				<div class="px-4 py-2 border-b retro-border flex items-center gap-2">
					<span class="text-confluent-accent font-mono text-xs">+</span>
					<span class="font-mono text-sm text-surface-300">ingest --source</span>
				</div>

					<div class="p-4 space-y-4">
						<!-- Quick presets -->
						<div class="flex items-center gap-2 flex-wrap">
							<span class="text-surface-500 font-mono text-xs">presets:</span>
							{#each presetSources as preset}
								<RetroButton
									size="sm"
									onclick={() => selectPreset(preset)}
								>
									{preset.name}<span class="text-surface-500 ml-1">({preset.size})</span>
								</RetroButton>
							{/each}
						</div>

						<form
							onsubmit={(e) => {
								e.preventDefault();
								handleIngest();
							}}
							class="space-y-3"
						>
							<div class="grid grid-cols-12 gap-3">
								<div class="col-span-2">
									<label class="block text-xs font-mono text-surface-500 mb-1">--type</label>
									<select
										bind:value={sourceType}
										class="w-full retro-input rounded"
									>
										<option value="sitemap">sitemap</option>
										<option value="github">github</option>
										<option value="url">url</option>
									</select>
								</div>
								<div class="col-span-3">
									<label class="block text-xs font-mono text-surface-500 mb-1">--name</label>
									<input
										type="text"
										bind:value={sourceName}
										placeholder="source-name"
										class="w-full retro-input rounded"
									/>
								</div>
								<div class="col-span-5">
									<label class="block text-xs font-mono text-surface-500 mb-1">--url</label>
									<input
										type="url"
										bind:value={sourceUrl}
										placeholder="https://..."
										class="w-full retro-input rounded"
									/>
								</div>
								<div class="col-span-2 flex items-end">
									<RetroButton
										type="submit"
										variant="primary"
										class="w-full"
										disabled={ingesting || !sourceName.trim() || !sourceUrl.trim()}
									>
										{ingesting ? 'running...' : 'run'}
									</RetroButton>
								</div>
							</div>
						</form>
					</div>
				</RetroCard>

			<!-- Success message for destructive operations -->
			{#if lastDestructiveResult}
				<RetroCard variant="glow-green" class="!p-0">
					<div class="p-3 font-mono text-sm text-emerald-400 flex items-center justify-between">
						<div class="flex items-center gap-2">
							<StatusIndicator status="active" size="sm" />
							{lastDestructiveResult.message}
						</div>
						<RetroButton size="sm" onclick={() => (lastDestructiveResult = null)}>×</RetroButton>
					</div>
				</RetroCard>
			{/if}

			<!-- Sync Status Panel (shown when out of sync) -->
			{#if syncStatus && (!syncStatus.synced || syncStatus.orphaned_collections.length > 0 || syncStatus.missing_sources.length > 0)}
				<RetroCard variant="glow-amber" noPadding>
					<div class="px-4 py-2 border-b retro-border flex items-center justify-between">
						<div class="flex items-center gap-2">
							<span class="text-amber-400 font-mono text-xs">⚠</span>
							<span class="font-mono text-sm text-amber-300">sync status: database ↔ qdrant</span>
						</div>
						<RetroButton
							size="sm"
							onclick={loadSyncStatus}
							disabled={syncLoading}
						>
							{syncLoading ? 'checking...' : '↻ refresh'}
						</RetroButton>
					</div>

					<div class="p-4 space-y-4">
						<!-- Orphaned collections in Qdrant -->
						{#if syncStatus.orphaned_collections.length > 0}
							<div class="bg-surface-900/50 rounded p-3">
								<div class="flex items-center justify-between mb-2">
									<span class="text-sm font-mono text-amber-400">
										<svg class="w-4 h-4 inline-block mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
											<path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
										</svg>
										Orphaned Collections ({syncStatus.orphaned_collections.length})
									</span>
									{#if activeDestructiveOp !== 'cleanup_orphans'}
										<button
											onclick={() => startDestructiveOp('cleanup_orphans')}
											disabled={cleanupLoading || activeDestructiveOp !== null}
											class="px-3 py-1 text-xs font-mono bg-amber-600/20 text-amber-400 hover:bg-amber-600/30 rounded border border-amber-600/50 disabled:opacity-50 flex items-center gap-1.5"
										>
											<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
												<path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
											</svg>
											cleanup orphans
										</button>
									{/if}
								</div>
								<p class="text-xs text-surface-400 mb-2">
									These collections exist in Qdrant but are not tracked in the database:
								</p>
								<div class="flex flex-wrap gap-2">
									{#each syncStatus.orphaned_collections as collection}
										<span class="px-2 py-1 text-xs font-mono bg-surface-700 text-amber-300 rounded">
											{collection}
										</span>
									{/each}
								</div>

								<!-- Inline confirmation for cleanup orphans -->
								{#if activeDestructiveOp === 'cleanup_orphans'}
									<div class="mt-4 p-4 bg-amber-900/30 border border-amber-600/50 rounded-lg">
										<div class="flex items-center gap-2 mb-3">
											<svg class="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
												<path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
											</svg>
											<span class="text-sm font-semibold text-amber-400">Confirm Deletion</span>
										</div>
										<p class="text-xs text-surface-300 mb-3">
											This will permanently delete all orphaned collections from Qdrant that are not tracked in the database.
										</p>
										<div class="mb-3">
											<label class="block text-xs font-mono text-surface-500 mb-1">
												Type <span class="text-amber-400 font-semibold">confirm delete</span> to proceed:
											</label>
											<input
												type="text"
												bind:value={destructiveConfirmText}
												placeholder="confirm delete"
												class="w-full px-3 py-2 bg-surface-900 border border-surface-600 rounded font-mono text-sm text-surface-100 placeholder-surface-600 focus:outline-none focus:border-amber-500"
											/>
										</div>
										<div class="flex gap-2">
											<button
												onclick={handleCleanupOrphans}
												disabled={cleanupLoading || destructiveConfirmText.toLowerCase() !== 'confirm delete'}
												class="px-4 py-2 text-sm font-mono bg-amber-600 hover:bg-amber-500 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
											>
												{#if cleanupLoading}
													<svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
														<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
														<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
													</svg>
													Deleting...
												{:else}
													<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
														<path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
													</svg>
													Delete Orphans
												{/if}
											</button>
											<button
												onclick={cancelDestructiveOp}
												disabled={cleanupLoading}
												class="px-4 py-2 text-sm font-mono bg-surface-700 hover:bg-surface-600 text-surface-300 rounded disabled:opacity-50"
											>
												Cancel
											</button>
										</div>
									</div>
								{/if}
							</div>
						{/if}

						<!-- Missing in Qdrant -->
						{#if syncStatus.missing_sources.length > 0}
							<div class="bg-surface-900/50 rounded p-3">
								<div class="flex items-center justify-between mb-2">
									<span class="text-sm font-mono text-red-400">
										<svg class="w-4 h-4 inline-block mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
											<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
										</svg>
										Missing in Qdrant ({syncStatus.missing_sources.length})
									</span>
									{#if activeDestructiveOp !== 'cleanup_stale'}
										<button
											onclick={() => startDestructiveOp('cleanup_stale')}
											disabled={cleanupLoading || activeDestructiveOp !== null}
											class="px-3 py-1 text-xs font-mono bg-red-600/20 text-red-400 hover:bg-red-600/30 rounded border border-red-600/50 disabled:opacity-50 flex items-center gap-1.5"
										>
											<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
												<path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
											</svg>
											remove stale entries
										</button>
									{/if}
								</div>
								<p class="text-xs text-surface-400 mb-2">
									These sources are in the database but have no vectors in Qdrant:
								</p>
								<div class="flex flex-wrap gap-2">
									{#each syncStatus.missing_sources as source}
										<span class="px-2 py-1 text-xs font-mono bg-surface-700 text-red-300 rounded">
											{source}
										</span>
									{/each}
								</div>

								<!-- Inline confirmation for cleanup stale -->
								{#if activeDestructiveOp === 'cleanup_stale'}
									<div class="mt-4 p-4 bg-red-900/30 border border-red-600/50 rounded-lg">
										<div class="flex items-center gap-2 mb-3">
											<svg class="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
												<path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
											</svg>
											<span class="text-sm font-semibold text-red-400">Confirm Deletion</span>
										</div>
										<p class="text-xs text-surface-300 mb-3">
											This will permanently remove stale database entries that have no corresponding vectors in Qdrant.
										</p>
										<div class="mb-3">
											<label class="block text-xs font-mono text-surface-500 mb-1">
												Type <span class="text-red-400 font-semibold">confirm delete</span> to proceed:
											</label>
											<input
												type="text"
												bind:value={destructiveConfirmText}
												placeholder="confirm delete"
												class="w-full px-3 py-2 bg-surface-900 border border-surface-600 rounded font-mono text-sm text-surface-100 placeholder-surface-600 focus:outline-none focus:border-red-500"
											/>
										</div>
										<div class="flex gap-2">
											<button
												onclick={handleCleanupStale}
												disabled={cleanupLoading || destructiveConfirmText.toLowerCase() !== 'confirm delete'}
												class="px-4 py-2 text-sm font-mono bg-red-600 hover:bg-red-500 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
											>
												{#if cleanupLoading}
													<svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
														<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
														<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
													</svg>
													Deleting...
												{:else}
													<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
														<path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
													</svg>
													Remove Stale Entries
												{/if}
											</button>
											<button
												onclick={cancelDestructiveOp}
												disabled={cleanupLoading}
												class="px-4 py-2 text-sm font-mono bg-surface-700 hover:bg-surface-600 text-surface-300 rounded disabled:opacity-50"
											>
												Cancel
											</button>
										</div>
									</div>
								{/if}
							</div>
						{/if}

						<!-- Danger zone -->
						<div class="pt-2 border-t border-amber-700/30">
							{#if activeDestructiveOp !== 'purge_all'}
								<button
									onclick={() => startDestructiveOp('purge_all')}
									disabled={cleanupLoading || activeDestructiveOp !== null}
									class="px-3 py-1 text-xs font-mono bg-red-900/50 hover:bg-red-800 text-red-400 rounded border border-red-700 disabled:opacity-50 inline-flex items-center gap-1.5"
								>
									<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
										<path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
									</svg>
									purge all data
								</button>
								<span class="text-xs text-surface-500 ml-2">Delete everything and start fresh</span>
							{/if}

							<!-- Inline confirmation for purge all -->
							{#if activeDestructiveOp === 'purge_all'}
								<div class="mt-2 p-4 bg-red-900/40 border border-red-500/50 rounded-lg">
									<div class="flex items-center gap-2 mb-3">
										<svg class="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
											<path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
										</svg>
										<span class="text-base font-bold text-red-400">⚠️ DANGER: Purge All Data</span>
									</div>
									<p class="text-sm text-red-300 mb-3">
										This will permanently delete <strong>ALL vectors</strong> from Qdrant and <strong>ALL database entries</strong>. This action cannot be undone!
									</p>
									<div class="mb-3">
										<label class="block text-xs font-mono text-surface-400 mb-1">
											Type <span class="text-red-400 font-semibold">confirm delete</span> to proceed:
										</label>
										<input
											type="text"
											bind:value={destructiveConfirmText}
											placeholder="confirm delete"
											class="w-full px-3 py-2 bg-surface-900 border border-red-600/50 rounded font-mono text-sm text-surface-100 placeholder-surface-600 focus:outline-none focus:border-red-500"
										/>
									</div>
									<div class="flex gap-2">
										<button
											onclick={handlePurgeAll}
											disabled={cleanupLoading || destructiveConfirmText.toLowerCase() !== 'confirm delete'}
											class="px-4 py-2 text-sm font-mono bg-red-600 hover:bg-red-500 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
										>
											{#if cleanupLoading}
												<svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
													<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
													<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
												</svg>
												Purging...
											{:else}
												<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
													<path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
												</svg>
												Purge All Data
											{/if}
										</button>
										<button
											onclick={cancelDestructiveOp}
											disabled={cleanupLoading}
											class="px-4 py-2 text-sm font-mono bg-surface-700 hover:bg-surface-600 text-surface-300 rounded disabled:opacity-50"
										>
											Cancel
										</button>
									</div>
								</div>
							{/if}
						</div>
					</div>
				</RetroCard>
			{/if}

				<!-- Collection Overview -->
				{#if collections && collections.collections.length > 0}
					<RetroCard noPadding>
						<div class="px-4 py-2 border-b retro-border flex items-center gap-2">
							<span class="text-blue-400 font-mono text-xs">🗄️</span>
							<span class="font-mono text-sm text-surface-300">qdrant collections</span>
						</div>
						<div class="p-4">
							{#each collections.collections as col}
								<RetroCard class="mb-4 last:mb-0">
									<!-- Header -->
									<div class="flex items-center justify-between mb-4">
										<div class="flex items-center gap-3">
											<span class="font-mono text-lg text-surface-100">{col.name}</span>
											<span
												class="px-2 py-0.5 text-xs rounded {col.status === 'green'
													? 'bg-emerald-600/20 text-emerald-400'
													: 'bg-amber-600/20 text-amber-400'}"
											>
												{col.status}
											</span>
											{#if col.optimizer_status === 'ok'}
												<span class="px-2 py-0.5 text-xs rounded bg-blue-600/20 text-blue-400">
													optimizer: ok
												</span>
											{/if}
										</div>
										<span class="font-mono text-2xl text-blue-400">
											{col.vectors_count.toLocaleString()}
											<span class="text-sm text-surface-500">vectors</span>
										</span>
									</div>

									<!-- Stats Grid -->
									<div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
										<div class="bg-surface-800 rounded p-3">
											<div class="text-xs text-surface-500 font-mono mb-1">Dimensions</div>
											<div class="text-lg font-mono text-purple-400">{col.dimensions}</div>
										</div>
										<div class="bg-surface-800 rounded p-3">
											<div class="text-xs text-surface-500 font-mono mb-1">Distance Metric</div>
											<div class="text-lg font-mono text-amber-400">{col.distance_metric}</div>
										</div>
										<div class="bg-surface-800 rounded p-3">
											<div class="text-xs text-surface-500 font-mono mb-1">Est. Size</div>
											<div class="text-lg font-mono text-surface-300">
												~{estimateStorageSize(col.vectors_count, col.dimensions)}
											</div>
										</div>
										<div class="bg-surface-800 rounded p-3">
											<div class="text-xs text-surface-500 font-mono mb-1">Segments</div>
											<div class="text-lg font-mono text-surface-300">{col.segments_count || 0}</div>
										</div>
									</div>

									<!-- HNSW Config (Pro Feature) -->
									{#if col.hnsw_config}
										<div class="border-t border-surface-700 pt-4 mt-4">
											<div class="text-xs text-surface-500 font-mono mb-2">
												📊 HNSW Index Configuration
												<span class="text-surface-600 ml-2">(Hierarchical Navigable Small World)</span>
											</div>
											<div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs font-mono">
												<div class="flex justify-between">
													<span class="text-surface-500">m:</span>
													<span class="text-emerald-400" title="Edges per node (higher = better recall)">{col.hnsw_config.m ?? 16}</span>
												</div>
												<div class="flex justify-between">
													<span class="text-surface-500">ef_construct:</span>
													<span class="text-emerald-400" title="Construction search width">{col.hnsw_config.ef_construct ?? 100}</span>
												</div>
												<div class="flex justify-between">
													<span class="text-surface-500">full_scan_threshold:</span>
													<span class="text-surface-300">{col.hnsw_config.full_scan_threshold?.toLocaleString() ?? '10k'}</span>
												</div>
												<div class="flex justify-between">
													<span class="text-surface-500">on_disk:</span>
													<span class={col.hnsw_config.on_disk ? 'text-amber-400' : 'text-emerald-400'}>
														{col.hnsw_config.on_disk ? 'yes' : 'no (RAM)'}
													</span>
												</div>
											</div>
										</div>
									{/if}

									<!-- Storage Mode -->
									<div class="flex gap-4 mt-4 text-xs font-mono flex-wrap">
										<div class="flex items-center gap-2">
											<span class="w-2 h-2 rounded-full {col.on_disk_vectors === true ? 'bg-amber-400' : 'bg-emerald-400'}"></span>
											<span class="text-surface-400">vectors: {col.on_disk_vectors === true ? 'disk' : 'RAM'}</span>
										</div>
										<div class="flex items-center gap-2">
											<span class="w-2 h-2 rounded-full {col.on_disk_payload === true ? 'bg-amber-400' : 'bg-emerald-400'}"></span>
											<span class="text-surface-400">payload: {col.on_disk_payload === true ? 'disk' : 'RAM'}</span>
										</div>
										{#if col.quantization_config}
											<div class="flex items-center gap-2">
												<span class="w-2 h-2 rounded-full bg-purple-400"></span>
												<span class="text-purple-400">quantization: {col.quantization_config.type}</span>
											</div>
										{:else}
											<div class="flex items-center gap-2">
												<span class="w-2 h-2 rounded-full bg-surface-500"></span>
											<span class="text-surface-500">no quantization</span>
										</div>
									{/if}
								</div>
								</RetroCard>
							{/each}
						</div>
					</RetroCard>
				{/if}

				<!-- Documents table -->
				<RetroCard noPadding>
					<div class="px-4 py-2 border-b retro-border flex items-center justify-between">
						<div class="flex items-center gap-2">
							<span class="text-blue-400 font-mono text-xs">&gt;</span>
							<span class="font-mono text-sm text-surface-300">document sources</span>
							<span class="text-surface-500 font-mono text-xs">({documents.length})</span>
						</div>
						<RetroButton
							size="sm"
							onclick={loadAll}
						>
							↻ refresh
						</RetroButton>
					</div>

					{#if loading}
						<div class="p-8 text-center font-mono text-surface-500">
							<span class="animate-pulse">loading...</span>
						</div>
					{:else if documents.length === 0}
						<div class="p-8 text-center font-mono text-surface-500">
							<svg
								class="w-12 h-12 mx-auto mb-3 opacity-50"
								fill="none"
								stroke="currentColor"
								viewBox="0 0 24 24"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="1.5"
									d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
								/>
							</svg>
							<p>no sources indexed</p>
							<p class="text-xs text-surface-600 mt-1">use --ingest to add documentation</p>
						</div>
					{:else}
						<!-- Table header -->
						<div
							class="grid grid-cols-12 gap-2 px-4 py-2 bg-surface-900/50 border-b border-surface-700 text-xs font-mono text-surface-500"
						>
							<div class="col-span-1">id</div>
							<div class="col-span-2">name</div>
							<div class="col-span-1">type</div>
							<div class="col-span-1">status</div>
							<div class="col-span-1 text-right">chunks</div>
							<div class="col-span-4">url</div>
							<div class="col-span-2 text-right">actions</div>
						</div>

						<!-- Table rows -->
						{#each documents as doc}
							{@const progress = activeIngestions.get(doc.id)}
							{@const startTime = ingestionStartTimes.get(doc.id)}
							<div class="border-b border-surface-700/50 last:border-b-0">
								<!-- Main row -->
								<div
									class="grid grid-cols-12 gap-2 px-4 py-2 text-sm font-mono items-center hover:bg-surface-700/30"
								>
									<div class="col-span-1 text-surface-500">#{doc.id}</div>
									<div class="col-span-2 text-surface-100 truncate font-mono" title={doc.name}>
										{doc.name}
									</div>
									<div class="col-span-1 text-surface-400 font-mono">{doc.source_type}</div>
									<div class="col-span-1 flex items-center gap-2">
										<StatusIndicator
											status={getStatusColor(doc.status)}
											size="sm"
											pulse={doc.status === 'indexing'}
										/>
										<span class="text-surface-300 font-mono text-xs">{doc.status}</span>
									</div>
									<div class="col-span-1 text-right text-surface-300 font-mono">
										{doc.document_count > 0 ? doc.document_count.toLocaleString() : '—'}
									</div>
									<div class="col-span-4 text-surface-500 truncate text-xs font-mono" title={doc.url}>
										{doc.url || '—'}
									</div>
							<div class="col-span-2 text-right flex items-center justify-end gap-2">
								{#if doc.status === 'indexing'}
									<button
										onclick={() => handleCancel(doc.id)}
										class="px-2 py-0.5 text-xs bg-amber-600/20 text-amber-400 hover:bg-amber-600/30 rounded border border-amber-600/50"
									>
										cancel
									</button>
								{/if}
								{#if confirmingDeleteId === doc.id}
									<button
										onclick={() => handleConfirmDelete(doc.id, doc.name)}
										class="px-2 py-0.5 text-xs bg-red-600 text-white hover:bg-red-500 rounded flex items-center gap-1"
									>
										<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
											<path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
										</svg>
										delete
									</button>
									<button
										onclick={handleCancelDelete}
										class="px-2 py-0.5 text-xs bg-surface-600 text-surface-200 hover:bg-surface-500 rounded"
									>
										cancel
									</button>
								{:else}
									<button
										onclick={() => handleDeleteClick(doc.id)}
										class="p-1.5 text-red-400 hover:text-red-300 hover:bg-red-600/20 rounded transition-colors"
										title="Delete source"
									>
										<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
											<path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
										</svg>
									</button>
								{/if}
							</div>
								</div>

								<!-- Progress section for active ingestions -->
								{#if doc.status === 'indexing' && progress}
									<div class="px-4 py-3 bg-surface-900/30 border-t border-surface-700/50">
										<div class="flex items-center gap-4 mb-2">
											<div class="flex-1 h-1.5 bg-surface-700 rounded-full overflow-hidden">
												<div
													class="h-full bg-emerald-500 transition-all duration-300"
													style="width: {progress.progress}%"
												></div>
											</div>
											{#if startTime}
												<span class="font-mono text-xs text-emerald-400"
													>{formatElapsedTime(startTime)}</span
												>
											{/if}
											<span class="font-mono text-xs text-surface-400">{progress.progress}%</span>
										</div>
										<div class="flex items-center gap-4 text-xs font-mono">
											<span class="text-amber-400">[{progress.stage}]</span>
											<span class="text-surface-400">{progress.message}</span>
										</div>
										{#if progress.pages_fetched || progress.chunks || progress.chunks_embedded}
											<div class="flex gap-4 mt-2 text-xs font-mono text-surface-500">
												{#if progress.pages_fetched && progress.pages_total}
													<span>fetch: {progress.pages_fetched}/{progress.pages_total}</span>
												{/if}
												{#if progress.pages_successful}
													<span>ok: {progress.pages_successful}</span>
												{/if}
												{#if progress.chunks}
													<span>chunks: {progress.chunks}</span>
												{/if}
												{#if progress.chunks_embedded}
													<span>embed: {progress.chunks_embedded}</span>
												{/if}
											</div>
										{/if}
									</div>
								{/if}

								<!-- Error/completed/cancelled displays -->
								{#if doc.status === 'error' && progress?.error}
									<div class="px-4 py-2 bg-red-900/10 border-t border-red-800/30">
										<span class="font-mono text-xs text-red-400">error: {progress.error}</span>
									</div>
								{/if}
								{#if progress?.status === 'completed' && progress.count !== undefined}
									<div class="px-4 py-2 bg-emerald-900/10 border-t border-emerald-800/30">
										<span class="font-mono text-xs text-emerald-400">
											✓ indexed {progress.count.toLocaleString()} chunks
											{#if progress.pages} from {progress.pages} pages{/if}
											{#if progress.elapsed_seconds} in {progress.elapsed_seconds}s{/if}
										</span>
								</div>
							{/if}
							{#if doc.status === 'cancelled' || progress?.status === 'cancelled'}
								<div class="px-4 py-2 bg-gray-900/10 border-t border-gray-800/30">
									<span class="font-mono text-xs text-gray-400">— cancelled</span>
								</div>
							{/if}
						</div>
					{/each}
				{/if}
			</RetroCard>

			<!-- ================================================================= -->
			<!-- SEARCH TAB -->
			<!-- ================================================================= -->
		{:else if activeTab === 'search'}
			<!-- Search interface -->
			<RetroCard noPadding>
				<div class="px-4 py-2 border-b retro-border flex items-center gap-2">
					<span class="text-blue-400 font-mono text-xs">🔍</span>
					<span class="font-mono text-sm text-surface-300">semantic vector search</span>
				</div>

				<div class="p-4 space-y-4">
					<RetroCard variant="elevated" class="!p-3 text-xs text-surface-400 font-mono">
						<p>
							<span class="text-emerald-400">How it works:</span> Your query is converted to an embedding
							vector, then compared against all stored document chunks using cosine similarity.
						</p>
					</RetroCard>

					<form
						onsubmit={(e) => {
							e.preventDefault();
							handleSearch();
						}}
						class="flex gap-3"
					>
						<input
							type="text"
							bind:value={searchQuery}
							placeholder="Search for anything..."
							class="flex-1 retro-input rounded"
						/>
						<select
							bind:value={searchK}
							class="retro-input rounded"
						>
							<option value={5}>Top 5</option>
							<option value={10}>Top 10</option>
							<option value={20}>Top 20</option>
						</select>
						<RetroButton
							type="submit"
							variant="primary"
							disabled={searchLoading || !searchQuery.trim()}
						>
							{searchLoading ? 'searching...' : 'search'}
						</RetroButton>
					</form>
				</div>
			</RetroCard>

			<!-- Search results -->
			{#if searchResults}
				<RetroCard noPadding>
					<div class="px-4 py-2 border-b retro-border flex items-center justify-between">
						<div class="flex items-center gap-2">
							<StatusIndicator status="active" size="sm" />
							<span class="font-mono text-sm text-surface-300"
								>{searchResults.total} results for "{searchResults.query}"</span
							>
						</div>
					</div>

						<div class="divide-y divide-surface-700/50">
							{#each searchResults.chunks as chunk, i}
								<div class="p-4 hover:bg-surface-700/20">
									<div class="flex items-start justify-between mb-2">
										<div class="flex items-center gap-3">
											<span class="text-surface-500 font-mono text-xs">#{i + 1}</span>
											<span
												class="font-mono text-xs px-2 py-0.5 rounded bg-surface-700 {getSimilarityColor(
													chunk.similarity_percent
												)}"
											>
												{chunk.similarity_percent}% match
											</span>
											<span class="text-surface-500 font-mono text-xs">
												from: {chunk.source_name}
											</span>
										</div>
										<button
											onclick={() => (selectedChunk = selectedChunk === chunk ? null : chunk)}
											class="text-xs font-mono text-surface-400 hover:text-surface-200"
										>
											{selectedChunk === chunk ? 'hide' : 'details'}
										</button>
									</div>

									<p class="text-sm text-surface-300 font-mono leading-relaxed">
										{chunk.content_preview}
									</p>

									{#if selectedChunk === chunk}
										<div
											class="mt-3 p-3 bg-surface-900 rounded text-xs font-mono space-y-2 border border-surface-700"
										>
											<div>
												<span class="text-surface-500">similarity_score:</span>
												<span class="text-blue-400 ml-2">{chunk.similarity_score.toFixed(4)}</span>
											</div>
											<div>
												<span class="text-surface-500">source:</span>
												<a
													href={chunk.source}
													target="_blank"
													class="text-blue-400 ml-2 hover:underline">{chunk.source}</a
												>
											</div>
											<div>
												<span class="text-surface-500">metadata:</span>
												<pre
													class="mt-1 text-surface-300 overflow-x-auto">{JSON.stringify(chunk.metadata, null, 2)}</pre>
											</div>
										</div>
									{/if}
								</div>
							{/each}
						</div>
					</RetroCard>
				{/if}

				<!-- ================================================================= -->
				<!-- BROWSE TAB -->
				<!-- ================================================================= -->
			{:else if activeTab === 'browse'}
				<!-- Browse controls -->
				<RetroCard noPadding>
					<div class="px-4 py-2 border-b retro-border flex items-center justify-between">
						<div class="flex items-center gap-2">
							<span class="text-purple-400 font-mono text-xs">📊</span>
							<span class="font-mono text-sm text-surface-300">vector browser</span>
						</div>
						<div class="flex items-center gap-3">
							<label class="flex items-center gap-2 text-xs font-mono text-surface-400">
								<input
									type="checkbox"
									bind:checked={showVectors}
									onchange={() => loadVectors()}
									class="rounded bg-surface-700 border-surface-600"
								/>
								show vectors
							</label>
							<button
								onclick={() => loadVectors()}
								class="text-surface-500 hover:text-surface-300 font-mono text-xs"
							>
								↻ refresh
							</button>
						</div>
					</div>

					<div class="p-3 bg-surface-900/50 text-xs text-surface-400 font-mono">
						<p>
							<span class="text-purple-400">Browse:</span> Explore the raw vectors stored in Qdrant.
						Each point represents a document chunk with its embedding.
					</p>
				</div>
			</RetroCard>

			<!-- Vector list -->
			{#if browseLoading}
				<RetroCard class="text-center py-8">
					<span class="font-mono text-surface-500 animate-pulse">loading vectors...</span>
				</RetroCard>
			{:else if browseResults}
				<RetroCard noPadding>
					<div class="px-4 py-2 border-b retro-border flex items-center justify-between">
						<span class="font-mono text-sm text-surface-300"
							>{browseResults.total_count} vectors in {browseResults.collection}</span
						>
						<div class="flex gap-2">
							{#if browseHistory.length > 0}
								<RetroButton
									size="sm"
									onclick={goBack}
								>
									← back
								</RetroButton>
							{/if}
							{#if browseResults.next_offset}
								<RetroButton
									size="sm"
									onclick={() => loadVectors(browseResults?.next_offset ?? undefined)}
								>
									next →
								</RetroButton>
							{/if}
						</div>
					</div>

						<div class="divide-y divide-surface-700/50">
							{#each browseResults.points as point}
								<div class="p-4">
									<div class="flex items-start justify-between mb-2">
										<span class="font-mono text-xs text-surface-500">id: {point.id}</span>
										{#if point.vector_dimensions}
											<span class="font-mono text-xs text-purple-400"
												>{point.vector_dimensions}d</span
											>
										{/if}
									</div>

									{#if point.payload?.page_content}
										<p class="text-sm text-surface-300 font-mono mb-2">
											{String(point.payload.page_content).slice(0, 300)}...
										</p>
									{/if}

									<div class="flex flex-wrap gap-2 text-xs font-mono">
										{#if point.payload?.source_name}
											<span class="px-2 py-0.5 bg-surface-700 text-surface-400 rounded"
												>{point.payload.source_name}</span
											>
										{/if}
										{#if point.payload?.source}
											<a
												href={String(point.payload.source)}
												target="_blank"
												class="text-blue-400 hover:underline truncate max-w-xs"
											>
												{String(point.payload.source).slice(0, 50)}...
											</a>
										{/if}
									</div>

									{#if showVectors && point.vector_preview}
										<div class="mt-2 p-2 bg-surface-900 rounded text-xs font-mono text-surface-500">
											<span class="text-purple-400">vector:</span>
											[{point.vector_preview.map((v) => v.toFixed(4)).join(', ')}...]
										</div>
									{/if}
								</div>
							{/each}
						</div>
					</RetroCard>
				{/if}

				<!-- ================================================================= -->
				<!-- PIPELINE TAB -->
				<!-- ================================================================= -->
			{:else if activeTab === 'pipeline'}
				<!-- Pipeline info -->
				{#if pipelineLoading}
					<RetroCard class="text-center py-8">
						<span class="font-mono text-surface-500 animate-pulse">loading pipeline info...</span>
					</RetroCard>
				{:else if pipelineInfo}
					<!-- RAG Overview -->
					<RetroCard noPadding>
						<div class="px-4 py-2 border-b retro-border flex items-center gap-2">
							<span class="text-amber-400 font-mono text-xs">⚡</span>
							<span class="font-mono text-sm text-surface-300"
								>RAG Pipeline: How Retrieval-Augmented Generation Works</span
							>
						</div>

						<div class="p-4">
							<div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
								<RetroCard variant="elevated">
									<h3 class="font-mono text-sm text-emerald-400 mb-2">🔧 Current Configuration</h3>
									<div class="space-y-2 text-xs font-mono">
										<div class="flex justify-between">
											<span class="text-surface-500">Embedding Model:</span>
											<span class="text-surface-300"
												>{pipelineInfo.embedding_config.model}</span
											>
										</div>
										<div class="flex justify-between">
											<span class="text-surface-500">Dimensions:</span>
											<span class="text-purple-400"
												>{pipelineInfo.embedding_config.dimensions}</span
											>
										</div>
										<div class="flex justify-between">
											<span class="text-surface-500">Hybrid Search:</span>
											<span
												class={pipelineInfo.hybrid_search_enabled
													? 'text-emerald-400'
													: 'text-red-400'}
											>
												{pipelineInfo.hybrid_search_enabled ? 'enabled' : 'disabled'}
											</span>
										</div>
									<div class="flex justify-between">
										<span class="text-surface-500">Reranking:</span>
										<span
											class={pipelineInfo.reranking_available
												? 'text-emerald-400'
												: 'text-amber-400'}
										>
											{pipelineInfo.reranking_available ? 'available' : 'not configured'}
										</span>
									</div>
								</div>
							</RetroCard>

							<RetroCard variant="elevated">
								<h3 class="font-mono text-sm text-blue-400 mb-2">📊 Retrieval Settings</h3>
								<div class="space-y-2 text-xs font-mono">
									<div class="flex justify-between">
										<span class="text-surface-500">Initial Candidates:</span>
										<span class="text-surface-300"
											>{pipelineInfo.retrieval_config.top_k_initial}</span
										>
									</div>
									<div class="flex justify-between">
										<span class="text-surface-500">Final Results:</span>
										<span class="text-surface-300"
											>{pipelineInfo.retrieval_config.top_k_final}</span
										>
									</div>
									<div class="flex justify-between">
										<span class="text-surface-500">Hybrid Alpha:</span>
										<span class="text-amber-400">{pipelineInfo.retrieval_config.hybrid_alpha}</span
										>
									</div>
									<div class="flex justify-between">
										<span class="text-surface-500">Query Expansions:</span>
										<span class="text-surface-300"
											>{pipelineInfo.retrieval_config.query_expansion_count}</span
										>
									</div>
								</div>
							</RetroCard>
						</div>
					</div>
				</RetroCard>

				<!-- Pipeline stages -->
				<RetroCard noPadding>
					<div class="px-4 py-2 border-b retro-border flex items-center gap-2">
						<span class="text-cyan-400 font-mono text-xs">🔄</span>
						<span class="font-mono text-sm text-surface-300">Pipeline Stages</span>
					</div>
					<div class="p-4">
						<div class="space-y-3">
							{#each pipelineInfo.pipeline_stages as stage, i}
								<div class="flex gap-4 items-start">
									<div
										class="w-8 h-8 rounded-full bg-surface-700 flex items-center justify-center text-sm font-mono text-surface-300 flex-shrink-0"
									>
										{i + 1}
									</div>
									<RetroCard variant="elevated" class="flex-1">
										<h4 class="font-mono text-sm text-emerald-400 mb-1">{stage.name}</h4>
										<p class="text-xs text-surface-400 mb-2">{stage.description}</p>
										{#if stage.example}
											<p class="text-xs text-surface-500 font-mono bg-surface-800 rounded p-2">
												{stage.example}
											</p>
										{/if}
									</RetroCard>
								</div>
							{/each}
						</div>
					</div>
				</RetroCard>

				<!-- Interactive Demo -->
				<RetroCard noPadding>
					<div class="px-4 py-2 border-b retro-border flex items-center gap-2">
						<span class="text-emerald-400 font-mono text-xs">🧪</span>
						<span class="font-mono text-sm text-surface-300">Interactive RAG Demo</span>
					</div>

					<div class="p-4 space-y-4">
						<form
							onsubmit={(e) => {
								e.preventDefault();
								runDemo();
							}}
								class="flex gap-3"
							>
								<input
									type="text"
									bind:value={demoQuery}
									placeholder="Enter a query to see the RAG pipeline in action..."
									class="flex-1 px-3 py-2 bg-surface-900 border border-surface-600 rounded font-mono text-sm text-surface-100 placeholder-surface-600 focus:outline-none focus:border-emerald-500"
								/>
								<RetroButton
									type="submit"
									variant="primary"
									disabled={demoLoading || !demoQuery.trim()}
								>
									{demoLoading ? 'running...' : 'run demo'}
								</RetroButton>
							</form>

							{#if demoResult}
								<div class="space-y-4">
									{#each demoResult.pipeline_steps as step}
										<div class="bg-surface-900 rounded-lg p-4 border border-surface-700">
											<div class="flex items-center gap-2 mb-2">
												<span
													class="w-6 h-6 rounded-full bg-emerald-600 flex items-center justify-center text-xs font-mono text-white"
													>{step.step}</span
												>
												<span class="font-mono text-sm text-emerald-400">{step.name}</span>
											</div>
											{#if step.description}
												<p class="text-xs text-surface-400 mb-2">{step.description}</p>
											{/if}
											{#if step.output}
												<div class="bg-surface-800 rounded p-2 text-xs font-mono">
													<pre class="text-surface-300 overflow-x-auto">{JSON.stringify(step.output, null, 2)}</pre>
												</div>
											{/if}
											{#if step.error}
												<p class="text-xs text-red-400">Error: {step.error}</p>
											{/if}
									</div>
								{/each}
							</div>
						{/if}
					</div>
				</RetroCard>

				<!-- Chunk Analytics -->
				{#if chunkAnalytics}
					<RetroCard noPadding>
						<div class="px-4 py-2 border-b retro-border flex items-center justify-between">
							<div class="flex items-center gap-2">
								<span class="text-cyan-400 font-mono text-xs">📈</span>
								<span class="font-mono text-sm text-surface-300">Chunk Analytics</span>
							</div>
							<RetroButton
								size="sm"
								onclick={loadAnalytics}
								disabled={analyticsLoading}
							>
								{analyticsLoading ? 'loading...' : '↻ refresh'}
							</RetroButton>
						</div>

						<div class="p-4">
								<div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
									<div class="bg-surface-900 rounded-lg p-3 border border-surface-700">
										<div class="text-xs text-surface-500 font-mono mb-1">Total Vectors</div>
										<div class="text-xl font-mono text-blue-400">
											{chunkAnalytics.total_vectors.toLocaleString()}
										</div>
									</div>
									<div class="bg-surface-900 rounded-lg p-3 border border-surface-700">
										<div class="text-xs text-surface-500 font-mono mb-1">Avg Chunk Size</div>
										<div class="text-xl font-mono text-purple-400">
											{chunkAnalytics.chunk_size_stats.avg_chars.toLocaleString()}
											<span class="text-xs text-surface-500">chars</span>
										</div>
									</div>
									<div class="bg-surface-900 rounded-lg p-3 border border-surface-700">
										<div class="text-xs text-surface-500 font-mono mb-1">Est. Tokens/Chunk</div>
										<div class="text-xl font-mono text-amber-400">
											~{chunkAnalytics.chunk_size_stats.avg_tokens_estimate}
										</div>
									</div>
									<div class="bg-surface-900 rounded-lg p-3 border border-surface-700">
										<div class="text-xs text-surface-500 font-mono mb-1">Index Health</div>
										<div class="text-xl font-mono {chunkAnalytics.index_health.optimizer_status === 'ok' ? 'text-emerald-400' : 'text-amber-400'}">
											{chunkAnalytics.index_health.optimizer_status}
										</div>
									</div>
								</div>

								<!-- Size Distribution -->
								<div class="mb-6">
									<h4 class="text-xs font-mono text-surface-500 mb-3">Chunk Size Distribution</h4>
									<div class="flex gap-2 h-24">
										{#each Object.entries(chunkAnalytics.size_distribution) as [range, count]}
											{@const maxCount = Math.max(...Object.values(chunkAnalytics.size_distribution))}
											{@const height = maxCount > 0 ? (count / maxCount) * 100 : 0}
											<div class="flex-1 flex flex-col items-center justify-end">
												<div
													class="w-full bg-gradient-to-t from-cyan-600 to-cyan-400 rounded-t transition-all"
													style="height: {height}%"
													title="{count} chunks"
												></div>
												<div class="text-xs font-mono text-surface-500 mt-1">{range}</div>
												<div class="text-xs font-mono text-surface-400">{count}</div>
											</div>
										{/each}
									</div>
								</div>

								<!-- Source Breakdown -->
								<div>
									<h4 class="text-xs font-mono text-surface-500 mb-3">Source Breakdown (sampled)</h4>
									<div class="space-y-2">
										{#each Object.entries(chunkAnalytics.sources).slice(0, 5) as [source, count]}
											{@const percentage = (count / chunkAnalytics.total_sampled) * 100}
											<div class="flex items-center gap-3">
												<div class="w-32 truncate text-xs font-mono text-surface-300" title={source}>
													{source}
												</div>
												<div class="flex-1 h-2 bg-surface-700 rounded-full overflow-hidden">
													<div
														class="h-full bg-emerald-500 transition-all"
														style="width: {percentage}%"
													></div>
												</div>
												<div class="text-xs font-mono text-surface-400 w-16 text-right">
													{count} ({percentage.toFixed(0)}%)
												</div>
											</div>
								{/each}
							</div>
						</div>
					</div>
				</RetroCard>
			{:else if analyticsLoading}
				<RetroCard class="text-center py-8">
					<span class="font-mono text-surface-500 animate-pulse">loading analytics...</span>
				</RetroCard>
			{/if}

			<!-- Embedding Comparison Tool -->
			<RetroCard noPadding>
				<div class="px-4 py-2 border-b retro-border flex items-center gap-2">
					<span class="text-purple-400 font-mono text-xs">🔬</span>
					<span class="font-mono text-sm text-surface-300">Embedding Similarity Comparison</span>
				</div>

				<div class="p-4 space-y-4">
					<p class="text-xs text-surface-400 font-mono">
								See how similar two texts are by comparing their embedding vectors.
							</p>

							<div class="grid grid-cols-2 gap-4">
								<div>
									<label class="block text-xs font-mono text-surface-500 mb-1">Text 1</label>
									<textarea
										bind:value={embedText1}
										placeholder="Enter first text..."
										rows="3"
										class="w-full px-3 py-2 bg-surface-900 border border-surface-600 rounded font-mono text-sm text-surface-100 placeholder-surface-600 focus:outline-none focus:border-purple-500"
									></textarea>
								</div>
								<div>
									<label class="block text-xs font-mono text-surface-500 mb-1">Text 2</label>
									<textarea
										bind:value={embedText2}
										placeholder="Enter second text..."
										rows="3"
										class="w-full px-3 py-2 bg-surface-900 border border-surface-600 rounded font-mono text-sm text-surface-100 placeholder-surface-600 focus:outline-none focus:border-purple-500"
									></textarea>
								</div>
							</div>

							<button
								onclick={handleEmbedCompare}
								disabled={embedLoading || !embedText1.trim() || !embedText2.trim()}
								class="px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:bg-surface-700 disabled:text-surface-500 text-white font-mono text-sm rounded transition-colors"
							>
								{embedLoading ? 'comparing...' : 'compare embeddings'}
							</button>

							{#if embedCompareResult}
								<div
									class="bg-surface-900 rounded-lg p-4 border border-surface-700 flex items-center gap-6"
								>
									<div class="text-center">
										<div
											class="text-3xl font-mono {getSimilarityColor(
												embedCompareResult.similarity_percent
											)}"
										>
											{embedCompareResult.similarity_percent}%
										</div>
										<div class="text-xs text-surface-500">similarity</div>
									</div>
									<div class="flex-1">
										<div class="h-4 bg-surface-700 rounded-full overflow-hidden">
											<div
												class="h-full bg-gradient-to-r from-purple-600 to-emerald-500 transition-all duration-500"
												style="width: {embedCompareResult.similarity_percent}%"
											></div>
										</div>
									</div>
									<div class="text-right">
										<div class="font-mono text-sm text-surface-300">
											{embedCompareResult.interpretation}
									</div>
									<div class="text-xs text-surface-500">
										cosine: {embedCompareResult.cosine_similarity.toFixed(4)}
									</div>
								</div>
							</div>
						{/if}
					</div>
				</RetroCard>
			{/if}

			<!-- ================================================================= -->
			<!-- AGENT GRAPH TAB -->
			<!-- ================================================================= -->
			{:else if activeTab === 'agents'}
				{#if agentGraphLoading}
					<div class="p-8 text-center font-mono text-surface-500">
						<span class="animate-pulse">loading agent graph...</span>
					</div>
				{:else if agentGraph}
					<RetroCard noPadding>
						<div class="px-4 py-2 border-b retro-border flex items-center gap-2">
							<span class="text-emerald-400 font-mono text-xs">🤖</span>
							<span class="font-mono text-sm text-surface-300">Multi-Agent System Architecture</span>
						</div>

						<div class="p-4 space-y-6">
							<!-- Description -->
							<div class="bg-surface-900 rounded-lg border border-surface-700 p-4">
								<pre class="text-xs text-surface-300 font-mono whitespace-pre-wrap">{agentGraph.description}</pre>
							</div>

							<!-- Agent Nodes -->
							<section>
								<h3 class="font-mono text-sm text-surface-300 mb-3">Available Agents</h3>
								<div class="grid grid-cols-1 md:grid-cols-2 gap-3">
									{#each agentGraph.nodes as node}
										<div class="retro-card rounded-lg p-3 flex items-start gap-3">
											<!-- Agent icon -->
											<div class="flex-shrink-0">
												<svg class="w-5 h-5 {node.color}" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
													<path stroke-linecap="round" stroke-linejoin="round" d={node.icon} />
												</svg>
											</div>

											<!-- Agent info -->
											<div class="flex-1 min-w-0">
												<h4 class="font-mono text-sm {node.color} font-bold">{node.label}</h4>
												<p class="text-xs text-surface-400 mt-1">{node.description}</p>
											</div>
										</div>
									{/each}
								</div>
							</section>

							<!-- Execution Paths -->
							<section>
								<h3 class="font-mono text-sm text-surface-300 mb-3">Execution Flow</h3>
								<div class="bg-surface-900 rounded-lg border border-surface-700 p-4 space-y-3">
									<p class="text-xs text-surface-400 font-mono mb-4">
										The router analyzes each query and determines the optimal execution path through the agent graph:
									</p>

									{#each agentGraph.edges as edge, i}
										{#if edge.from_node === 'START'}
											<div class="flex items-center gap-3 text-xs font-mono">
												<span class="text-violet-400">[START]</span>
												<svg class="w-4 h-4 text-surface-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
													<path stroke-linecap="round" stroke-linejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
												</svg>
												<span class="text-violet-400">{edge.to_node}</span>
											</div>
										{:else if edge.to_node === 'END'}
											<div class="flex items-center gap-3 text-xs font-mono">
												<span class="text-emerald-400">{edge.from_node}</span>
												<svg class="w-4 h-4 text-surface-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
													<path stroke-linecap="round" stroke-linejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
												</svg>
												<span class="text-surface-500">[END]</span>
											</div>
										{:else}
											<div class="flex items-start gap-3 text-xs font-mono">
												<span class="{agentGraph.nodes.find(n => n.name === edge.from_node)?.color || 'text-surface-400'}">{edge.from_node}</span>
												<svg class="w-4 h-4 text-surface-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
													<path stroke-linecap="round" stroke-linejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
												</svg>
												<div class="flex-1">
													<span class="{agentGraph.nodes.find(n => n.name === edge.to_node)?.color || 'text-surface-400'}">{edge.to_node}</span>
													{#if edge.condition}
														<div class="text-surface-500 mt-0.5">
															<span class="text-surface-600">if</span> {edge.condition}
														</div>
													{/if}
												</div>
											</div>
										{/if}
									{/each}
								</div>
							</section>

							<!-- Real-time Observation -->
							<section class="bg-amber-900/20 border border-amber-800/30 rounded-lg p-4">
								<div class="flex items-start gap-3">
									<svg class="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
										<path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
									</svg>
									<div>
										<h4 class="font-mono text-sm text-amber-400 font-bold mb-1">See It In Action</h4>
										<p class="text-xs text-surface-300 font-mono">
											Watch the agent pipeline in real-time by opening the <span class="text-emerald-400">Agent Activity</span> sidebar
											in the Chat page. You'll see each agent activate, the routing decisions, and the data flowing through the system.
										</p>
									</div>
								</div>
							</section>
						</div>
					</RetroCard>
				{:else}
					<div class="p-8 text-center font-mono text-surface-500">
						<p>Failed to load agent graph</p>
						<RetroButton size="sm" onclick={loadAgentGraph} class="mt-4">
							retry
						</RetroButton>
					</div>
				{/if}
			{/if}
		</div>
	</div>
</div>
