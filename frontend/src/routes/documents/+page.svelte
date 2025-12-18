<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { getDocuments, ingestDocument, deleteDocument, cancelIngestion, getIngestionStatus, type DocumentSource } from '$lib/api';

	let documents = $state<DocumentSource[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);
	let ingesting = $state(false);

	// Form state
	let sourceType = $state<'sitemap' | 'github' | 'url'>('sitemap');
	let sourceName = $state('');
	let sourceUrl = $state('');

	// Active ingestion tracking
	let activeIngestions = $state<Map<number, IngestionProgress>>(new Map());
	let ingestionStartTimes = $state<Map<number, number>>(new Map());
	let pollInterval: ReturnType<typeof setInterval> | null = null;
	let timerInterval: ReturnType<typeof setInterval> | null = null;
	let currentTime = $state(Date.now());

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

	// Preset sources
	const presetSources = [
		{ name: 'htmx', type: 'sitemap' as const, url: 'https://htmx.org/sitemap.xml', size: '~180' },
		{ name: 'fastapi', type: 'sitemap' as const, url: 'https://fastapi.tiangolo.com/sitemap.xml', size: '~150' },
		{ name: 'kafka', type: 'sitemap' as const, url: 'https://kafka.apache.org/sitemap.xml', size: '~500' },
		{ name: 'confluent', type: 'sitemap' as const, url: 'https://docs.confluent.io/home/sitemap.xml', size: '5k+' }
	];

	async function loadDocuments() {
		loading = true;
		error = null;
		try {
			documents = await getDocuments();
			const indexingDocs = documents.filter(d => d.status === 'indexing');
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

	function formatElapsedTime(startTime: number): string {
		const elapsed = Math.floor((currentTime - startTime) / 1000);
		const mins = Math.floor(elapsed / 60);
		const secs = elapsed % 60;
		return mins > 0 ? `${mins}m ${secs.toString().padStart(2, '0')}s` : `${secs}s`;
	}

	async function pollProgress() {
		const indexingIds = documents.filter(d => d.status === 'indexing').map(d => d.id);
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
				if (status.status === 'completed' || status.status === 'error' || status.status === 'cancelled') {
					await loadDocuments();
				}
			} catch (e) { console.error(`Failed to get status for ${id}:`, e); }
		}
		activeIngestions = new Map(activeIngestions);
	}

	async function handleIngest() {
		if (!sourceName.trim() || !sourceUrl.trim()) return;
		ingesting = true;
		error = null;
		try {
			const result = await ingestDocument({ source_type: sourceType, name: sourceName, url: sourceUrl });
			activeIngestions.set(result.source_id, { status: 'running', progress: 0, stage: 'init', message: 'Starting...' });
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

	async function handleDelete(id: number) {
		if (!confirm('Delete this source?')) return;
		try {
			await deleteDocument(id);
			activeIngestions.delete(id);
			ingestionStartTimes.delete(id);
			activeIngestions = new Map(activeIngestions);
			ingestionStartTimes = new Map(ingestionStartTimes);
			await loadDocuments();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to delete';
		}
	}

	function selectPreset(preset: typeof presetSources[0]) {
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

	onMount(() => { loadDocuments(); });
	onDestroy(() => { stopPolling(); });
</script>

<div class="flex flex-col h-full bg-surface-900">
	<!-- Terminal-style header -->
	<header class="px-6 py-4 border-b border-surface-700 bg-surface-800/50">
		<div class="flex items-center gap-3">
			<span class="text-emerald-400 font-mono text-sm">$</span>
			<h1 class="font-mono text-lg text-surface-100">kgpt/documents</h1>
			<span class="text-surface-500 font-mono text-sm">--manage-sources</span>
		</div>
	</header>

	<div class="flex-1 overflow-y-auto p-6">
		<div class="max-w-5xl mx-auto space-y-6">

			<!-- Ingest form - compact terminal style -->
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

					<form onsubmit={(e) => { e.preventDefault(); handleIngest(); }} class="space-y-3">
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

			<!-- Error display -->
			{#if error}
				<div class="bg-red-900/20 border border-red-800 rounded p-3 font-mono text-sm text-red-400">
					<span class="text-red-500">error:</span> {error}
				</div>
			{/if}

			<!-- Documents table -->
			<section class="bg-surface-800 border border-surface-700 rounded overflow-hidden">
				<div class="px-4 py-2 border-b border-surface-700 flex items-center justify-between">
					<div class="flex items-center gap-2">
						<span class="text-blue-400 font-mono text-xs">&gt;</span>
						<span class="font-mono text-sm text-surface-300">sources</span>
						<span class="text-surface-500 font-mono text-xs">({documents.length})</span>
					</div>
					<button onclick={loadDocuments} class="text-surface-500 hover:text-surface-300 font-mono text-xs">
						↻ refresh
					</button>
				</div>

				{#if loading}
					<div class="p-8 text-center font-mono text-surface-500">
						<span class="animate-pulse">loading...</span>
					</div>
				{:else if documents.length === 0}
					<div class="p-8 text-center font-mono text-surface-500">
						<svg class="w-12 h-12 mx-auto mb-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
						</svg>
						<p>no sources indexed</p>
						<p class="text-xs text-surface-600 mt-1">use --ingest to add documentation</p>
					</div>
				{:else}
					<!-- Table header -->
					<div class="grid grid-cols-12 gap-2 px-4 py-2 bg-surface-900/50 border-b border-surface-700 text-xs font-mono text-surface-500">
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
							<div class="grid grid-cols-12 gap-2 px-4 py-2 text-sm font-mono items-center hover:bg-surface-700/30">
								<div class="col-span-1 text-surface-500">#{doc.id}</div>
								<div class="col-span-2 text-surface-100 truncate" title={doc.name}>{doc.name}</div>
								<div class="col-span-1 text-surface-400">{doc.source_type}</div>
								<div class="col-span-1 {getStatusColor(doc.status)}">{doc.status}</div>
								<div class="col-span-1 text-right text-surface-300">
									{doc.document_count > 0 ? doc.document_count.toLocaleString() : '—'}
								</div>
								<div class="col-span-4 text-surface-500 truncate text-xs" title={doc.url}>
									{doc.url || '—'}
								</div>
								<div class="col-span-2 text-right space-x-2">
									{#if doc.status === 'indexing'}
										<button
											onclick={() => handleCancel(doc.id)}
											class="px-2 py-0.5 text-xs bg-amber-600/20 text-amber-400 hover:bg-amber-600/30 rounded border border-amber-600/50"
										>
											cancel
										</button>
									{/if}
									<button
										onclick={() => handleDelete(doc.id)}
										class="px-2 py-0.5 text-xs bg-red-600/20 text-red-400 hover:bg-red-600/30 rounded border border-red-600/50"
									>
										rm
									</button>
								</div>
							</div>

							<!-- Progress section for active ingestions -->
							{#if doc.status === 'indexing' && progress}
								<div class="px-4 py-3 bg-surface-900/30 border-t border-surface-700/50">
									<div class="flex items-center gap-4 mb-2">
										<!-- Progress bar -->
										<div class="flex-1 h-1.5 bg-surface-700 rounded-full overflow-hidden">
											<div
												class="h-full bg-emerald-500 transition-all duration-300"
												style="width: {progress.progress}%"
											></div>
										</div>
										<!-- Timer -->
										{#if startTime}
											<span class="font-mono text-xs text-emerald-400">{formatElapsedTime(startTime)}</span>
										{/if}
										<span class="font-mono text-xs text-surface-400">{progress.progress}%</span>
									</div>

									<!-- Status line -->
									<div class="flex items-center gap-4 text-xs font-mono">
										<span class="text-amber-400">[{progress.stage}]</span>
										<span class="text-surface-400">{progress.message}</span>
									</div>

									<!-- Stats -->
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

							<!-- Error display -->
							{#if doc.status === 'error' && progress?.error}
								<div class="px-4 py-2 bg-red-900/10 border-t border-red-800/30">
									<span class="font-mono text-xs text-red-400">error: {progress.error}</span>
								</div>
							{/if}

							<!-- Completed summary -->
							{#if progress?.status === 'completed' && progress.count !== undefined}
								<div class="px-4 py-2 bg-emerald-900/10 border-t border-emerald-800/30">
									<span class="font-mono text-xs text-emerald-400">
										✓ indexed {progress.count.toLocaleString()} chunks
										{#if progress.pages} from {progress.pages} pages{/if}
										{#if progress.elapsed_seconds} in {progress.elapsed_seconds}s{/if}
									</span>
								</div>
							{/if}

							<!-- Cancelled display -->
							{#if doc.status === 'cancelled' || progress?.status === 'cancelled'}
								<div class="px-4 py-2 bg-gray-900/10 border-t border-gray-800/30">
									<span class="font-mono text-xs text-gray-400">— cancelled</span>
								</div>
							{/if}
						</div>
					{/each}
				{/if}
			</section>

		</div>
	</div>
</div>
