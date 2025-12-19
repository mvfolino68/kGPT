<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import {
		getDocuments,
		ingestDocument,
		ingestFile,
		deleteDocument,
		cancelIngestion,
		getIngestionStatus,
		getCollections,
		searchDocuments,
		browseVectors,
		getRAGPipelineInfo,
		runRAGDemo,
		compareEmbeddings,
		getSyncStatus,
		cleanupOrphanVectors,
		cleanupStaleEntries,
		purgeAllData,
		getChunkAnalytics,
		suggestName,
		type DocumentSource,
		type SourceType
	} from '$lib/api';
	import { Header, HeaderStatus } from '$lib/components';
	import { Hint } from '$lib/components/hints';
	import {
		IngestionForm,
		DocumentsTable,
		CollectionsOverview,
		SyncStatusPanel,
		SearchTab,
		BrowseTab,
		PipelineTab,
		type Tab,
		type IngestionProgress,
		type DestructiveOperation,
		type CollectionsResponse,
		type VectorSearchResponse,
		type VectorBrowseResponse,
		type RAGPipelineInfo,
		type RAGDemoResponse,
		type SyncStatusResponse,
		type ChunkAnalytics
	} from '$lib/components/documents';
	import { Card, Icon, IconButton, StatusDot, Button, Page, Tabs } from '$lib/components';

	// =========================================================================
	// Tab Navigation
	// =========================================================================
	const validTabs: Tab[] = ['sources', 'search', 'browse', 'pipeline'];

	function getTabFromUrl(): Tab {
		const tabParam = $page.url.searchParams.get('tab');
		if (tabParam && validTabs.includes(tabParam as Tab)) {
			return tabParam as Tab;
		}
		return 'sources';
	}

	let activeTab = $state<Tab>(getTabFromUrl());

	function setActiveTab(tab: Tab) {
		activeTab = tab;
		const url = new URL($page.url);
		if (tab === 'sources') {
			url.searchParams.delete('tab');
		} else {
			url.searchParams.set('tab', tab);
		}
		goto(url.toString(), { replaceState: true, noScroll: true });
	}

	// Keep UI in sync with URL (back/forward, manual edits).
	$effect(() => {
		const urlTab = getTabFromUrl();
		if (urlTab !== activeTab) activeTab = urlTab;
	});

	// =========================================================================
	// Sources Tab State
	// =========================================================================
	let documents = $state<DocumentSource[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);
	let ingesting = $state(false);

	// Form state
	let sourceType = $state<SourceType>('github');
	let sourceName = $state('');
	let sourceUrl = $state('');
	let rawTextContent = $state('');
	let useSmartNaming = $state(true);
	let nameSuggestions = $state<string[]>([]);
	let smartName = $state<string | null>(null);
	let fetchingName = $state(false);
	let selectedFile = $state<File | null>(null);
	let urlDebounceTimer: ReturnType<typeof setTimeout> | null = null;

	// Delete confirmation
	let confirmingDeleteId = $state<number | null>(null);

	// Ingestion tracking
	let activeIngestions = $state<Map<number, IngestionProgress>>(new Map());
	let ingestionStartTimes = $state<Map<number, number>>(new Map());
	let pollInterval: ReturnType<typeof setInterval> | null = null;
	let timerInterval: ReturnType<typeof setInterval> | null = null;
	let currentTime = $state(Date.now());

	// Collections & Sync
	let collections = $state<CollectionsResponse | null>(null);
	let collectionsLoading = $state(false);
	let syncStatus = $state<SyncStatusResponse | null>(null);
	let syncLoading = $state(false);
	let cleanupLoading = $state(false);
	let activeDestructiveOp = $state<DestructiveOperation>(null);
	let destructiveConfirmText = $state('');
	let lastDestructiveResult = $state<{ type: DestructiveOperation; message: string } | null>(null);

	// =========================================================================
	// Search Tab State
	// =========================================================================
	let searchQuery = $state('');
	let searchResults = $state<VectorSearchResponse | null>(null);
	let searchLoading = $state(false);
	let searchK = $state(10);

	// =========================================================================
	// Browse Tab State
	// =========================================================================
	let browseResults = $state<VectorBrowseResponse | null>(null);
	let browseLoading = $state(false);
	let showVectors = $state(false);
	let browseHistory = $state<string[]>([]);

	// =========================================================================
	// Pipeline Tab State
	// =========================================================================
	let pipelineInfo = $state<RAGPipelineInfo | null>(null);
	let pipelineLoading = $state(false);
	let demoQuery = $state('');
	let demoResult = $state<RAGDemoResponse | null>(null);
	let demoLoading = $state(false);
	let chunkAnalytics = $state<ChunkAnalytics | null>(null);
	let analyticsLoading = $state(false);
	let embedText1 = $state('');
	let embedText2 = $state('');
	let embedCompareResult = $state<{ cosine_similarity: number; similarity_percent: number; interpretation: string } | null>(null);
	let embedLoading = $state(false);

	// =========================================================================
	// Data Loading Functions
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
						activeIngestions.set(doc.id, { status: 'running', progress: 0, stage: 'loading', message: 'Checking progress...' });
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

	async function loadAll() {
		await Promise.all([loadDocuments(), loadCollections(), loadSyncStatus()]);
	}

	// =========================================================================
	// Polling
	// =========================================================================
	function startPolling() {
		if (pollInterval) return;
		pollInterval = setInterval(pollProgress, 1000);
		if (!timerInterval) {
			timerInterval = setInterval(() => { currentTime = Date.now(); }, 1000);
		}
	}

	function stopPolling() {
		if (pollInterval) { clearInterval(pollInterval); pollInterval = null; }
		if (timerInterval) { clearInterval(timerInterval); timerInterval = null; }
	}

	async function pollProgress() {
		const indexingIds = documents.filter((d) => d.status === 'indexing').map((d) => d.id);
		for (const [id] of activeIngestions) {
			if (!indexingIds.includes(id)) {
				const progress = activeIngestions.get(id);
				if (progress && progress.status === 'running') indexingIds.push(id);
			}
		}
		if (indexingIds.length === 0) { stopPolling(); return; }

		for (const id of indexingIds) {
			try {
				const status = await getIngestionStatus(id);
				activeIngestions.set(id, status as IngestionProgress);
				if (['completed', 'error', 'cancelled'].includes(status.status)) {
					await loadAll();
				}
			} catch (e) {
				console.error(`Failed to get status for ${id}:`, e);
			}
		}
		activeIngestions = new Map(activeIngestions);
	}

	// =========================================================================
	// Smart Naming
	// =========================================================================
	async function fetchNameSuggestions(url: string | null, content: string | null) {
		fetchingName = true;
		try {
			const request: { url?: string; content?: string; source_type: SourceType } = { source_type: sourceType };
			if (sourceType === 'text') {
				if (!content || content.trim().length === 0) { nameSuggestions = []; smartName = null; return; }
				request.content = content;
			} else {
				if (!url || !url.startsWith('http')) { nameSuggestions = []; smartName = null; return; }
				request.url = url;
			}
			const response = await suggestName(request);
			nameSuggestions = response.suggestions;
			smartName = response.smart_name;
			if (useSmartNaming && !sourceName && smartName) {
				sourceName = smartName;
			}
		} catch (e) {
			console.error('Failed to fetch name suggestions:', e);
		} finally {
			fetchingName = false;
		}
	}

	function handleUrlInput(url: string) {
		sourceUrl = url;
		if (urlDebounceTimer) clearTimeout(urlDebounceTimer);
		if (url && url.startsWith('http')) {
			urlDebounceTimer = setTimeout(() => fetchNameSuggestions(url, null), 500);
		} else {
			nameSuggestions = []; smartName = null;
		}
	}

	function handleTextContentInput(content: string) {
		rawTextContent = content;
		if (urlDebounceTimer) clearTimeout(urlDebounceTimer);
		if (content && content.trim().length > 0) {
			urlDebounceTimer = setTimeout(() => fetchNameSuggestions(null, content), 500);
		} else {
			nameSuggestions = []; smartName = null;
		}
	}

	// =========================================================================
	// Ingestion Actions
	// =========================================================================
	async function handleIngest() {
		if (sourceType === 'text' && !rawTextContent.trim()) return;
		if (sourceType === 'file' && !selectedFile && !rawTextContent.trim()) return;
		if (sourceType !== 'text' && sourceType !== 'file' && !sourceUrl.trim()) return;

		ingesting = true;
		error = null;
		try {
			let result;

			if (sourceType === 'file' && selectedFile) {
				result = await ingestFile(selectedFile, {
					name: sourceName || undefined,
					collection_name: 'kgpt_docs', // Default collection
					auto_name: useSmartNaming && !sourceName
				});
			} else {
				result = await ingestDocument({
					source_type: sourceType,
					name: sourceName || undefined,
					url: sourceType === 'text' ? rawTextContent : sourceUrl,
					auto_name: useSmartNaming && !sourceName
				});
			}

			activeIngestions.set(result.source_id, { status: 'running', progress: 0, stage: 'init', message: 'Starting...' });
			activeIngestions = new Map(activeIngestions);
			ingestionStartTimes.set(result.source_id, Date.now());
			ingestionStartTimes = new Map(ingestionStartTimes);
			startPolling();
			sourceName = ''; sourceUrl = ''; rawTextContent = ''; selectedFile = null; nameSuggestions = []; smartName = null;
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
			if (progress) { progress.status = 'cancelling'; progress.message = 'Cancelling...'; activeIngestions = new Map(activeIngestions); }
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to cancel';
		}
	}

	async function handleConfirmDelete(id: number, _sourceName: string) {
		try {
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

	// =========================================================================
	// Destructive Operations
	// =========================================================================
	function startDestructiveOp(op: DestructiveOperation) { activeDestructiveOp = op; destructiveConfirmText = ''; lastDestructiveResult = null; }
	function cancelDestructiveOp() { activeDestructiveOp = null; destructiveConfirmText = ''; }

	async function handleCleanupOrphans() {
		if (destructiveConfirmText.toLowerCase() !== 'confirm delete') return;
		cleanupLoading = true;
		try {
			const result = await cleanupOrphanVectors();
			error = null;
			lastDestructiveResult = { type: 'cleanup_orphans', message: `Cleaned up ${result.orphans_found} orphan sources, ${result.total_vectors_deleted} vectors deleted` };
			await loadAll();
		} catch (e) { error = e instanceof Error ? e.message : 'Cleanup failed'; }
		finally { cleanupLoading = false; activeDestructiveOp = null; destructiveConfirmText = ''; }
	}

	async function handleCleanupStale() {
		if (destructiveConfirmText.toLowerCase() !== 'confirm delete') return;
		cleanupLoading = true;
		try {
			const result = await cleanupStaleEntries();
			error = null;
			lastDestructiveResult = { type: 'cleanup_stale', message: `Cleaned up ${result.entries_cleaned} stale database entries` };
			await loadAll();
		} catch (e) { error = e instanceof Error ? e.message : 'Cleanup failed'; }
		finally { cleanupLoading = false; activeDestructiveOp = null; destructiveConfirmText = ''; }
	}

	async function handlePurgeAll() {
		if (destructiveConfirmText.toLowerCase() !== 'confirm delete') return;
		cleanupLoading = true;
		try {
			const result = await purgeAllData();
			error = null;
			lastDestructiveResult = { type: 'purge_all', message: `Purged ${result.db_entries_deleted} sources and ${result.vectors_deleted} vectors` };
			await loadAll();
		} catch (e) { error = e instanceof Error ? e.message : 'Purge failed'; }
		finally { cleanupLoading = false; activeDestructiveOp = null; destructiveConfirmText = ''; }
	}

	// =========================================================================
	// Search Functions
	// =========================================================================
	async function handleSearch() {
		if (!searchQuery.trim()) return;
		searchLoading = true;
		try {
			searchResults = await searchDocuments(searchQuery, { k: searchK });
		} catch (e) { error = e instanceof Error ? e.message : 'Search failed'; }
		finally { searchLoading = false; }
	}

	// =========================================================================
	// Browse Functions
	// =========================================================================
	async function loadVectors(offset?: string) {
		browseLoading = true;
		try {
			browseResults = await browseVectors({ limit: 20, offset, withVectors: showVectors });
			if (offset) browseHistory = [...browseHistory, offset];
		} catch (e) { error = e instanceof Error ? e.message : 'Failed to load vectors'; }
		finally { browseLoading = false; }
	}

	function goBack() {
		if (browseHistory.length > 0) {
			browseHistory.pop();
			const prevOffset = browseHistory[browseHistory.length - 1] || undefined;
			loadVectors(prevOffset);
		}
	}

	// =========================================================================
	// Pipeline Functions
	// =========================================================================
	async function loadPipelineInfo() {
		pipelineLoading = true;
		try { pipelineInfo = await getRAGPipelineInfo(); }
		catch (e) { console.error('Failed to load pipeline info:', e); }
		finally { pipelineLoading = false; }
	}

	async function runDemo() {
		if (!demoQuery.trim()) return;
		demoLoading = true;
		try { demoResult = await runRAGDemo(demoQuery); }
		catch (e) { error = e instanceof Error ? e.message : 'Demo failed'; }
		finally { demoLoading = false; }
	}

	async function loadAnalytics() {
		analyticsLoading = true;
		try { chunkAnalytics = await getChunkAnalytics(); }
		catch (e) { console.error('Failed to load analytics:', e); }
		finally { analyticsLoading = false; }
	}

	async function handleEmbedCompare() {
		if (!embedText1.trim() || !embedText2.trim()) return;
		embedLoading = true;
		try { embedCompareResult = await compareEmbeddings(embedText1, embedText2); }
		catch (e) { error = e instanceof Error ? e.message : 'Comparison failed'; }
		finally { embedLoading = false; }
	}

	// =========================================================================
	// Lifecycle
	// =========================================================================
	onMount(() => { loadAll(); });
	onDestroy(() => { stopPolling(); });

	$effect(() => {
		if (activeTab === 'browse' && !browseResults) loadVectors();
		if (activeTab === 'pipeline' && !pipelineInfo) { loadPipelineInfo(); loadAnalytics(); }
	});
</script>

<svelte:head>
	<title>Vector Store - kGPT</title>
</svelte:head>

<Page
	title="Vector Store"
	subtitle="RAG Document & Embedding Management"
	loading={loading && documents.length === 0}
	error={error}
	status={syncStatus ? { connected: syncStatus.synced, label: syncStatus.synced ? 'Synced' : 'Sync Warning' } : null}
>
	{#snippet headerActions()}
	{/snippet}

	{#snippet subNavigation()}
		<Tabs
			active={activeTab}
			items={[
				{ id: 'sources', label: 'Sources' },
				{ id: 'search', label: 'Search' },
				{ id: 'browse', label: 'Browse' },
				{ id: 'pipeline', label: 'RAG Pipeline' }
			]}
			on:change={(e) => setActiveTab(e.detail as Tab)}
		/>
	{/snippet}

	<!-- Success message for destructive operations -->
	{#if lastDestructiveResult}
		<Card variant="success" padding="sm" class="mb-6">
			<div class="flex items-center gap-2 text-sm">
				<StatusDot status="success" size="sm" />
				<span class="text-success flex-1">{lastDestructiveResult.message}</span>
				<IconButton
					variant="ghost"
					size="sm"
					title="Dismiss message"
					onclick={() => lastDestructiveResult = null}
				>
					<Icon name="x" size="sm" />
				</IconButton>
			</div>
		</Card>
	{/if}

	<!-- Tab Content -->
	{#if activeTab === 'sources'}
		<div
			id="tabpanel-sources"
			role="tabpanel"
			aria-labelledby="tab-sources"
			tabindex="0"
			class="space-y-6"
		>
		<IngestionForm
			{sourceType}
			{sourceName}
			{sourceUrl}
			{rawTextContent}
			{useSmartNaming}
			{nameSuggestions}
			{smartName}
			{fetchingName}
			{ingesting}
			hasFile={!!selectedFile}
			onFileChange={(file) => selectedFile = file}
			onSourceTypeChange={(type) => { sourceType = type; nameSuggestions = []; smartName = null; sourceName = ''; selectedFile = null; }}
			onSourceNameChange={(name) => sourceName = name}
			onUrlInput={handleUrlInput}
			onTextContentInput={handleTextContentInput}
			onSmartNamingChange={(enabled) => useSmartNaming = enabled}
			onSelectSuggestion={(name) => sourceName = name}
			onSubmit={handleIngest}
		/>

		{#if syncStatus}
			<SyncStatusPanel
				{syncStatus}
				{syncLoading}
				{cleanupLoading}
				{activeDestructiveOp}
				{destructiveConfirmText}
				onRefresh={loadSyncStatus}
				onStartDestructiveOp={startDestructiveOp}
				onCancelDestructiveOp={cancelDestructiveOp}
				onConfirmTextChange={(text) => destructiveConfirmText = text}
				onCleanupOrphans={handleCleanupOrphans}
				onCleanupStale={handleCleanupStale}
				onPurgeAll={handlePurgeAll}
			/>
		{/if}

		{#if collections}
			<CollectionsOverview {collections} />
		{/if}

		<DocumentsTable
			{documents}
			{loading}
			{activeIngestions}
			{ingestionStartTimes}
			{currentTime}
			{confirmingDeleteId}
			onRefresh={loadAll}
			onCancel={handleCancel}
			onDeleteClick={(id) => confirmingDeleteId = id}
			onConfirmDelete={handleConfirmDelete}
			onCancelDelete={() => confirmingDeleteId = null}
		/>
		</div>

	{:else if activeTab === 'search'}
		<div
			id="tabpanel-search"
			role="tabpanel"
			aria-labelledby="tab-search"
			tabindex="0"
			class="space-y-6"
		>
		<SearchTab
			{searchQuery}
			{searchResults}
			{searchLoading}
			{searchK}
			onQueryChange={(query) => searchQuery = query}
			onKChange={(k) => searchK = k}
			onSearch={handleSearch}
		/>
		</div>

	{:else if activeTab === 'browse'}
		<div
			id="tabpanel-browse"
			role="tabpanel"
			aria-labelledby="tab-browse"
			tabindex="0"
			class="space-y-6"
		>
		<BrowseTab
			{browseResults}
			{browseLoading}
			{showVectors}
			{browseHistory}
			onLoadVectors={loadVectors}
			onToggleVectors={(show) => { showVectors = show; loadVectors(); }}
			onGoBack={goBack}
		/>
		</div>

	{:else if activeTab === 'pipeline'}
		<div
			id="tabpanel-pipeline"
			role="tabpanel"
			aria-labelledby="tab-pipeline"
			tabindex="0"
			class="space-y-6"
		>
		<PipelineTab
			{pipelineInfo}
			{pipelineLoading}
			{demoQuery}
			{demoResult}
			{demoLoading}
			{chunkAnalytics}
			{analyticsLoading}
			{embedText1}
			{embedText2}
			{embedCompareResult}
			{embedLoading}
			onDemoQueryChange={(query) => demoQuery = query}
			onRunDemo={runDemo}
			onLoadAnalytics={loadAnalytics}
			onEmbedText1Change={(text) => embedText1 = text}
			onEmbedText2Change={(text) => embedText2 = text}
			onEmbedCompare={handleEmbedCompare}
		/>
		</div>
	{/if}
</Page>

<!-- Contextual Hint -->
<Hint
	id="documents"
	title="Build Your Knowledge Base"
	description="Add documentation, websites, or files here. The AI uses this content to provide more accurate, context-aware responses."
/>
