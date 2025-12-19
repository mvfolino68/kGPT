<script lang="ts">
	import { StatusIndicator, Button, IconButton } from '$lib/components';
	import { getStatusColor, type DocumentSource, type IngestionProgress } from './types';

	interface Props {
		documents: DocumentSource[];
		loading: boolean;
		activeIngestions: Map<number, IngestionProgress>;
		ingestionStartTimes: Map<number, number>;
		currentTime: number;
		confirmingDeleteId: number | null;
		onRefresh: () => void;
		onCancel: (id: number) => void;
		onDeleteClick: (id: number) => void;
		onConfirmDelete: (id: number, name: string) => void;
		onCancelDelete: () => void;
	}

	let {
		documents,
		loading,
		activeIngestions,
		ingestionStartTimes,
		currentTime,
		confirmingDeleteId,
		onRefresh,
		onCancel,
		onDeleteClick,
		onConfirmDelete,
		onCancelDelete
	}: Props = $props();

	function formatElapsedTime(startTime: number): string {
		const elapsed = Math.floor((currentTime - startTime) / 1000);
		const mins = Math.floor(elapsed / 60);
		const secs = elapsed % 60;
		return mins > 0 ? `${mins}m ${secs.toString().padStart(2, '0')}s` : `${secs}s`;
	}
</script>

<div class="panel overflow-hidden">
	<div class="panel-header flex items-center justify-between">
		<div class="flex items-center gap-2">
			<span class="text-surface-400 text-xs">&gt;</span>
			<span class="text-sm text-surface-300">Document Sources</span>
			<span class="text-surface-500 text-xs">({documents.length})</span>
		</div>
		<Button variant="ghost" size="sm" onclick={onRefresh}>
			Refresh
		</Button>
	</div>

	{#if loading}
		<div class="p-8 text-center text-surface-500">
			<span class="animate-pulse">Loading...</span>
		</div>
	{:else if documents.length === 0}
		<div class="p-8 text-center text-surface-500">
			<svg class="w-12 h-12 mx-auto mb-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
			</svg>
			<p>No sources indexed</p>
			<p class="text-xs text-surface-600 mt-1">Add documentation above to get started</p>
		</div>
	{:else}
		<!-- Table header -->
		<div class="grid grid-cols-12 gap-2 px-4 py-2 bg-surface-900/50 text-[10px] font-bold uppercase tracking-wider text-surface-500">
			<div class="col-span-1">ID</div>
			<div class="col-span-2">Name</div>
			<div class="col-span-1">Type</div>
			<div class="col-span-1">Status</div>
			<div class="col-span-1 text-right">Chunks</div>
			<div class="col-span-4">URL</div>
			<div class="col-span-2 text-right">Actions</div>
		</div>

		<!-- Table rows -->
		{#each documents as doc}
			{@const progress = activeIngestions.get(doc.id)}
			{@const startTime = ingestionStartTimes.get(doc.id)}
			<div class="">
				<div class="grid grid-cols-12 gap-2 px-4 py-2.5 text-sm items-center hover:bg-surface-800/30 transition-colors">
					<div class="col-span-1 text-surface-500 text-xs">#{doc.id}</div>
					<div class="col-span-2 text-surface-100 truncate" title={doc.name}>{doc.name}</div>
					<div class="col-span-1 text-surface-400 text-xs">{doc.source_type}</div>
					<div class="col-span-1 flex items-center gap-2">
						<StatusIndicator status={getStatusColor(doc.status)} size="sm" pulse={doc.status === 'indexing'} />
						<span class="text-surface-300 text-xs">{doc.status}</span>
					</div>
					<div class="col-span-1 text-right text-surface-300 text-xs">
						{doc.document_count > 0 ? doc.document_count.toLocaleString() : '—'}
					</div>
					<div class="col-span-4 text-surface-500 truncate text-xs" title={doc.url}>
						{doc.url || '—'}
					</div>
					<div class="col-span-2 text-right flex items-center justify-end gap-2">
						{#if doc.status === 'indexing'}
							<Button variant="warning" size="xs" onclick={() => onCancel(doc.id)}>
								Cancel
							</Button>
						{/if}
						{#if confirmingDeleteId === doc.id}
							<Button variant="danger-solid" size="xs" onclick={() => onConfirmDelete(doc.id, doc.name)}>
								<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
									<path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
								</svg>
								Delete
							</Button>
							<Button variant="default" size="xs" onclick={onCancelDelete}>
								Cancel
							</Button>
						{:else}
							<IconButton
								variant="danger"
								size="sm"
								title="Delete source"
								onclick={() => onDeleteClick(doc.id)}
							>
								<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
									<path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
								</svg>
							</IconButton>
						{/if}
					</div>
				</div>

				<!-- Progress section -->
				{#if doc.status === 'indexing' && progress}
					<div class="px-4 py-3 bg-surface-900/30">
						<div class="flex items-center gap-4 mb-2">
							<div class="flex-1 h-1.5 bg-surface-800 rounded-full overflow-hidden">
								<div class="h-full bg-surface-500 transition-all duration-300" style="width: {progress.progress}%"></div>
							</div>
							{#if startTime}
								<span class="text-xs text-surface-300">{formatElapsedTime(startTime)}</span>
							{/if}
							<span class="text-xs text-surface-400">{progress.progress}%</span>
						</div>
						<div class="flex items-center gap-4 text-xs">
							<span class="text-surface-400">[{progress.stage}]</span>
							<span class="text-surface-500">{progress.message}</span>
						</div>
						{#if progress.pages_fetched || progress.chunks || progress.chunks_embedded}
							<div class="flex gap-4 mt-2 text-xs text-surface-500">
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
					<div class="px-4 py-2 bg-red-500/5">
						<span class="text-xs text-red-400/80">Error: {progress.error}</span>
					</div>
				{/if}

				<!-- Completed display -->
				{#if progress?.status === 'completed' && progress.count !== undefined}
					<div class="px-4 py-2 bg-emerald-500/5">
						<span class="text-xs text-emerald-400/80">
							Indexed {progress.count.toLocaleString()} chunks
							{#if progress.pages} from {progress.pages} pages{/if}
							{#if progress.elapsed_seconds} in {progress.elapsed_seconds}s{/if}
						</span>
					</div>
				{/if}

				<!-- Cancelled display -->
				{#if doc.status === 'cancelled' || progress?.status === 'cancelled'}
					<div class="px-4 py-2 bg-surface-800/50">
						<span class="text-xs text-surface-500">Cancelled</span>
					</div>
				{/if}
			</div>
		{/each}
	{/if}
</div>
