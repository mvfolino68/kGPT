<script lang="ts">
	import { Panel, LoadingState, EmptyState, StatusPill, Button, IconButton, DeleteConfirmButton } from '$lib/components/ui';
	import { getStatusColor, type DocumentSource, type IngestionProgress } from './types';

	interface Props {
		documents: DocumentSource[];
		loading: boolean;
		activeIngestions: Map<number, IngestionProgress>;
		ingestionStartTimes: Map<number, number>;
		currentTime: number;
		onRefresh: () => void;
		onCancel: (id: number) => void;
		onConfirmDelete: (id: number, name: string) => void;
	}

	let {
		documents,
		loading,
		activeIngestions,
		ingestionStartTimes,
		currentTime,
		onRefresh,
		onCancel,
		onConfirmDelete
	}: Props = $props();

	function formatElapsedTime(startTime: number): string {
		const elapsed = Math.floor((currentTime - startTime) / 1000);
		const mins = Math.floor(elapsed / 60);
		const secs = elapsed % 60;
		return mins > 0 ? `${mins}m ${secs.toString().padStart(2, '0')}s` : `${secs}s`;
	}

	function toPillStatus(status: ReturnType<typeof getStatusColor>): 'success' | 'warning' | 'error' | 'inactive' | 'info' {
		if (status === 'active') return 'success';
		if (status === 'warning') return 'warning';
		if (status === 'error') return 'error';
		return 'inactive';
	}

	function formatStatusLabel(raw: string): string {
		// known statuses: indexed, indexing, error, cancelled, pending
		if (!raw) return 'Unknown';
		return raw.charAt(0).toUpperCase() + raw.slice(1);
	}
</script>

<Panel
	title="Document Sources"
	subtitle="({documents.length})"
>
	{#snippet actions()}
		<Button variant="ghost" size="sm" onclick={onRefresh}>
			Refresh
		</Button>
	{/snippet}
	{#snippet children()}
	{#if loading}
		<div class="p-8 text-center">
			<LoadingState message="Loading..." showSpinner={true} size="sm" class="animate-pulse" />
		</div>
	{:else if documents.length === 0}
		<EmptyState
			icon="document"
			title="No sources indexed"
			description="Add documentation above to get started"
		/>
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
						<StatusPill
							status={toPillStatus(getStatusColor(doc.status))}
							label={formatStatusLabel(doc.status)}
							pulse={doc.status === 'indexing'}
						/>
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
						<DeleteConfirmButton
							size="sm"
							itemId={doc.id}
							title="Delete source"
							onConfirm={() => onConfirmDelete(doc.id, doc.name)}
						/>
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
					<div class="px-4 py-2 bg-error-bg">
						<span class="text-xs text-error">Error: {progress.error}</span>
					</div>
				{/if}

				<!-- Completed display -->
				{#if progress?.status === 'completed' && progress.count !== undefined}
					<div class="px-4 py-2 bg-success-bg">
						<span class="text-xs text-success">
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
	{/snippet}
</Panel>
