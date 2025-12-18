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
		type DocumentSource,
		type CollectionsResponse,
		type VectorSearchResponse,
		type VectorBrowseResponse,
		type RAGPipelineInfo,
		type RAGDemoResponse,
		type ChunkResult,
		type SyncStatusResponse,
		type ChunkAnalytics
	} from '$lib/api';

	// =========================================================================
	// State
	// =========================================================================

	// Tab navigation
	type Tab = 'sources' | 'search' | 'browse' | 'pipeline';
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
		const colors: Record<string, string> = {
			indexed: 'text-emerald-400',
			indexing: 'text-amber-400',
			error: 'text-red-400',
			cancelled: 'text-gray-400',
			pending: 'text-gray-500'
		};
		return colors[status] || 'text-gray-500';
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
	});
</script>

<div class="flex flex-col h-full bg-surface-900">
	<!-- Header with stats -->
	<header class="px-6 py-4 border-b border-surface-700 bg-surface-800/50">
		<div class="flex items-center justify-between">
			<div class="flex items-center gap-3">
				<span class="text-emerald-400 font-mono text-sm">$</span>
				<h1 class="font-mono text-lg text-surface-100">kgpt/documents</h1>
				<span class="text-surface-500 font-mono text-sm">--vector-store</span>
			</div>

			<!-- Quick stats -->
			<div class="flex items-center gap-6 text-xs font-mono">
				{#if syncStatus}
					<div class="flex items-center gap-2">
						<span class="text-surface-500">sync:</span>
						{#if syncStatus.synced}
							<span class="text-emerald-400">✓ synced</span>
						{:else}
							<span class="text-amber-400">⚠ out of sync</span>
						{/if}
					</div>
				{/if}
				{#if collections}
					<div class="flex items-center gap-2">
						<span class="text-surface-500">collections:</span>
						<span class="text-emerald-400">{collections.total_collections}</span>
					</div>
					<div class="flex items-center gap-2">
						<span class="text-surface-500">vectors:</span>
						<span class="text-blue-400">{collections.total_vectors.toLocaleString()}</span>
					</div>
				{/if}
				<div class="flex items-center gap-2">
					<span class="text-surface-500">sources:</span>
					<span class="text-purple-400">{documents.length}</span>
				</div>
			</div>
		</div>

		<!-- Tab navigation -->
		<nav class="flex gap-1 mt-4">
			{#each [
				{ id: 'sources' as Tab, label: 'Sources', icon: '📁' },
				{ id: 'search' as Tab, label: 'Vector Search', icon: '🔍' },
				{ id: 'browse' as Tab, label: 'Browse Vectors', icon: '📊' },
				{ id: 'pipeline' as Tab, label: 'RAG Pipeline', icon: '⚡' }
			] as tab}
				<button
					onclick={() => (activeTab = tab.id)}
					class="px-4 py-2 font-mono text-sm rounded-t transition-colors {activeTab === tab.id
						? 'bg-surface-700 text-surface-100 border-t border-x border-surface-600'
						: 'text-surface-400 hover:text-surface-200 hover:bg-surface-800'}"
				>
					<span class="mr-2">{tab.icon}</span>
					{tab.label}
				</button>
			{/each}
		</nav>
	</header>

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
				<section class="bg-surface-800 border border-surface-700 rounded">
					<div class="px-4 py-2 border-b border-surface-700 flex items-center gap-2">
						<span class="text-emerald-400 font-mono text-xs">+</span>
						<span class="font-mono text-sm text-surface-300">ingest --source</span>
					</div>

					<div class="p-4 space-y-4">
						<!-- Quick presets -->
						<div class="flex items-center gap-2 flex-wrap">
							<span class="text-surface-500 font-mono text-xs">presets:</span>
							{#each presetSources as preset}
								<button
									type="button"
									onclick={() => selectPreset(preset)}
									class="px-2 py-1 font-mono text-xs bg-surface-700 hover:bg-surface-600 text-surface-300 rounded border border-surface-600 hover:border-surface-500 transition-colors"
								>
									{preset.name}<span class="text-surface-500 ml-1">({preset.size})</span>
								</button>
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
										class="w-full px-2 py-1.5 bg-surface-900 border border-surface-600 rounded font-mono text-sm text-surface-100 focus:outline-none focus:border-emerald-500"
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
										class="w-full px-2 py-1.5 bg-surface-900 border border-surface-600 rounded font-mono text-sm text-surface-100 placeholder-surface-600 focus:outline-none focus:border-emerald-500"
									/>
								</div>
								<div class="col-span-5">
									<label class="block text-xs font-mono text-surface-500 mb-1">--url</label>
									<input
										type="url"
										bind:value={sourceUrl}
										placeholder="https://..."
										class="w-full px-2 py-1.5 bg-surface-900 border border-surface-600 rounded font-mono text-sm text-surface-100 placeholder-surface-600 focus:outline-none focus:border-emerald-500"
									/>
								</div>
								<div class="col-span-2 flex items-end">
									<button
										type="submit"
										disabled={ingesting || !sourceName.trim() || !sourceUrl.trim()}
										class="w-full px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 disabled:bg-surface-700 disabled:text-surface-500 text-white font-mono text-sm rounded transition-colors"
									>
										{ingesting ? 'running...' : 'run'}
									</button>
								</div>
							</div>
						</form>
					</div>
				</section>

			<!-- Success message for destructive operations -->
			{#if lastDestructiveResult}
				<div class="bg-emerald-900/20 border border-emerald-700 rounded p-3 font-mono text-sm text-emerald-400 flex items-center justify-between">
					<div class="flex items-center gap-2">
						<span class="text-emerald-500">✓</span>
						{lastDestructiveResult.message}
					</div>
					<button onclick={() => (lastDestructiveResult = null)} class="text-emerald-500 hover:text-emerald-400">×</button>
				</div>
			{/if}

			<!-- Sync Status Panel (shown when out of sync) -->
			{#if syncStatus && (!syncStatus.synced || syncStatus.orphaned_sources.length > 0 || syncStatus.missing_sources.length > 0)}
				<section class="bg-amber-900/20 border border-amber-700 rounded">
					<div class="px-4 py-2 border-b border-amber-700/50 flex items-center justify-between">
						<div class="flex items-center gap-2">
							<span class="text-amber-400 font-mono text-xs">⚠</span>
							<span class="font-mono text-sm text-amber-300">sync status: database ↔ qdrant</span>
						</div>
						<button
							onclick={loadSyncStatus}
							disabled={syncLoading}
							class="text-amber-400 hover:text-amber-300 font-mono text-xs"
						>
							{syncLoading ? 'checking...' : '↻ refresh'}
						</button>
					</div>

					<div class="p-4 space-y-4">
						<!-- Orphaned vectors in Qdrant -->
						{#if syncStatus.orphaned_sources.length > 0}
							<div class="bg-surface-900/50 rounded p-3">
								<div class="flex items-center justify-between mb-2">
									<span class="text-sm font-mono text-amber-400">
										<svg class="w-4 h-4 inline-block mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
											<path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
										</svg>
										Orphaned in Qdrant ({syncStatus.orphaned_sources.length})
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
									These sources exist in Qdrant but are not tracked in the database:
								</p>
								<div class="flex flex-wrap gap-2">
									{#each syncStatus.orphaned_sources as source}
										<span class="px-2 py-1 text-xs font-mono bg-surface-700 text-amber-300 rounded">
											{source}
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
											This will permanently delete all orphaned vectors from Qdrant that are not tracked in the database.
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
				</section>
			{/if}

				<!-- Collection Overview -->
				{#if collections && collections.collections.length > 0}
					<section class="bg-surface-800 border border-surface-700 rounded">
						<div class="px-4 py-2 border-b border-surface-700 flex items-center gap-2">
							<span class="text-blue-400 font-mono text-xs">🗄️</span>
							<span class="font-mono text-sm text-surface-300">qdrant collections</span>
						</div>
						<div class="p-4">
							{#each collections.collections as col}
								<div class="bg-surface-900 rounded-lg p-4 border border-surface-700">
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
								</div>
							{/each}
						</div>
					</section>
				{/if}

				<!-- Documents table -->
				<section class="bg-surface-800 border border-surface-700 rounded overflow-hidden">
					<div class="px-4 py-2 border-b border-surface-700 flex items-center justify-between">
						<div class="flex items-center gap-2">
							<span class="text-blue-400 font-mono text-xs">&gt;</span>
							<span class="font-mono text-sm text-surface-300">document sources</span>
							<span class="text-surface-500 font-mono text-xs">({documents.length})</span>
						</div>
						<button
							onclick={loadAll}
							class="text-surface-500 hover:text-surface-300 font-mono text-xs"
						>
							↻ refresh
						</button>
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
									<div class="col-span-2 text-surface-100 truncate" title={doc.name}>
										{doc.name}
									</div>
									<div class="col-span-1 text-surface-400">{doc.source_type}</div>
									<div class="col-span-1 {getStatusColor(doc.status)}">{doc.status}</div>
									<div class="col-span-1 text-right text-surface-300">
										{doc.document_count > 0 ? doc.document_count.toLocaleString() : '—'}
									</div>
									<div class="col-span-4 text-surface-500 truncate text-xs" title={doc.url}>
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
				</section>

				<!-- ================================================================= -->
				<!-- SEARCH TAB -->
				<!-- ================================================================= -->
			{:else if activeTab === 'search'}
				<!-- Search interface -->
				<section class="bg-surface-800 border border-surface-700 rounded">
					<div class="px-4 py-2 border-b border-surface-700 flex items-center gap-2">
						<span class="text-blue-400 font-mono text-xs">🔍</span>
						<span class="font-mono text-sm text-surface-300">semantic vector search</span>
					</div>

					<div class="p-4 space-y-4">
						<div class="bg-surface-900/50 rounded-lg p-3 text-xs text-surface-400 font-mono">
							<p>
								<span class="text-emerald-400">How it works:</span> Your query is converted to an embedding
								vector, then compared against all stored document chunks using cosine similarity.
							</p>
						</div>

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
								class="flex-1 px-3 py-2 bg-surface-900 border border-surface-600 rounded font-mono text-sm text-surface-100 placeholder-surface-600 focus:outline-none focus:border-blue-500"
							/>
							<select
								bind:value={searchK}
								class="px-3 py-2 bg-surface-900 border border-surface-600 rounded font-mono text-sm text-surface-100"
							>
								<option value={5}>Top 5</option>
								<option value={10}>Top 10</option>
								<option value={20}>Top 20</option>
							</select>
							<button
								type="submit"
								disabled={searchLoading || !searchQuery.trim()}
								class="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-surface-700 disabled:text-surface-500 text-white font-mono text-sm rounded transition-colors"
							>
								{searchLoading ? 'searching...' : 'search'}
							</button>
						</form>
					</div>
				</section>

				<!-- Search results -->
				{#if searchResults}
					<section class="bg-surface-800 border border-surface-700 rounded">
						<div class="px-4 py-2 border-b border-surface-700 flex items-center justify-between">
							<div class="flex items-center gap-2">
								<span class="text-emerald-400 font-mono text-xs">✓</span>
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
					</section>
				{/if}

				<!-- ================================================================= -->
				<!-- BROWSE TAB -->
				<!-- ================================================================= -->
			{:else if activeTab === 'browse'}
				<!-- Browse controls -->
				<section class="bg-surface-800 border border-surface-700 rounded">
					<div class="px-4 py-2 border-b border-surface-700 flex items-center justify-between">
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
				</section>

				<!-- Vector list -->
				{#if browseLoading}
					<div class="p-8 text-center font-mono text-surface-500">
						<span class="animate-pulse">loading vectors...</span>
					</div>
				{:else if browseResults}
					<section class="bg-surface-800 border border-surface-700 rounded">
						<div class="px-4 py-2 border-b border-surface-700 flex items-center justify-between">
							<span class="font-mono text-sm text-surface-300"
								>{browseResults.total_count} vectors in {browseResults.collection}</span
							>
							<div class="flex gap-2">
								{#if browseHistory.length > 0}
									<button
										onclick={goBack}
										class="px-3 py-1 text-xs font-mono bg-surface-700 hover:bg-surface-600 text-surface-300 rounded"
									>
										← back
									</button>
								{/if}
								{#if browseResults.next_offset}
									<button
										onclick={() => loadVectors(browseResults?.next_offset ?? undefined)}
										class="px-3 py-1 text-xs font-mono bg-surface-700 hover:bg-surface-600 text-surface-300 rounded"
									>
										next →
									</button>
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
					</section>
				{/if}

				<!-- ================================================================= -->
				<!-- PIPELINE TAB -->
				<!-- ================================================================= -->
			{:else if activeTab === 'pipeline'}
				<!-- Pipeline info -->
				{#if pipelineLoading}
					<div class="p-8 text-center font-mono text-surface-500">
						<span class="animate-pulse">loading pipeline info...</span>
					</div>
				{:else if pipelineInfo}
					<!-- RAG Overview -->
					<section class="bg-surface-800 border border-surface-700 rounded">
						<div class="px-4 py-2 border-b border-surface-700 flex items-center gap-2">
							<span class="text-amber-400 font-mono text-xs">⚡</span>
							<span class="font-mono text-sm text-surface-300"
								>RAG Pipeline: How Retrieval-Augmented Generation Works</span
							>
						</div>

						<div class="p-4">
							<div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
								<div class="bg-surface-900 rounded-lg p-4 border border-surface-700">
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
								</div>

								<div class="bg-surface-900 rounded-lg p-4 border border-surface-700">
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
								</div>
							</div>

							<!-- Pipeline stages -->
							<h3 class="font-mono text-sm text-surface-300 mb-3">Pipeline Stages</h3>
							<div class="space-y-3">
								{#each pipelineInfo.pipeline_stages as stage, i}
									<div class="flex gap-4 items-start">
										<div
											class="w-8 h-8 rounded-full bg-surface-700 flex items-center justify-center text-sm font-mono text-surface-300 flex-shrink-0"
										>
											{i + 1}
										</div>
										<div class="flex-1 bg-surface-900 rounded-lg p-3 border border-surface-700">
											<h4 class="font-mono text-sm text-emerald-400 mb-1">{stage.name}</h4>
											<p class="text-xs text-surface-400 mb-2">{stage.description}</p>
											{#if stage.example}
												<p class="text-xs text-surface-500 font-mono bg-surface-800 rounded p-2">
													{stage.example}
												</p>
											{/if}
										</div>
									</div>
								{/each}
							</div>
						</div>
					</section>

					<!-- Interactive Demo -->
					<section class="bg-surface-800 border border-surface-700 rounded">
						<div class="px-4 py-2 border-b border-surface-700 flex items-center gap-2">
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
								<button
									type="submit"
									disabled={demoLoading || !demoQuery.trim()}
									class="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:bg-surface-700 disabled:text-surface-500 text-white font-mono text-sm rounded transition-colors"
								>
									{demoLoading ? 'running...' : 'run demo'}
								</button>
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
					</section>

					<!-- Chunk Analytics -->
					{#if chunkAnalytics}
						<section class="bg-surface-800 border border-surface-700 rounded">
							<div class="px-4 py-2 border-b border-surface-700 flex items-center justify-between">
								<div class="flex items-center gap-2">
									<span class="text-cyan-400 font-mono text-xs">📈</span>
									<span class="font-mono text-sm text-surface-300">Chunk Analytics</span>
								</div>
								<button
									onclick={loadAnalytics}
									disabled={analyticsLoading}
									class="text-surface-500 hover:text-surface-300 font-mono text-xs"
								>
									{analyticsLoading ? 'loading...' : '↻ refresh'}
								</button>
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
						</section>
					{:else if analyticsLoading}
						<div class="p-8 text-center font-mono text-surface-500">
							<span class="animate-pulse">loading analytics...</span>
						</div>
					{/if}

					<!-- Embedding Comparison Tool -->
					<section class="bg-surface-800 border border-surface-700 rounded">
						<div class="px-4 py-2 border-b border-surface-700 flex items-center gap-2">
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
					</section>
				{/if}
			{/if}
		</div>
	</div>
</div>
