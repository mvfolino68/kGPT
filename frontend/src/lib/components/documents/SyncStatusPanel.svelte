<script lang="ts">
	import { StatusIndicator } from '$lib/components';
	import type { SyncStatusResponse, DestructiveOperation } from './types';

	interface Props {
		syncStatus: SyncStatusResponse;
		syncLoading: boolean;
		cleanupLoading: boolean;
		activeDestructiveOp: DestructiveOperation;
		destructiveConfirmText: string;
		onRefresh: () => void;
		onStartDestructiveOp: (op: DestructiveOperation) => void;
		onCancelDestructiveOp: () => void;
		onConfirmTextChange: (text: string) => void;
		onCleanupOrphans: () => void;
		onCleanupStale: () => void;
		onPurgeAll: () => void;
	}

	let {
		syncStatus,
		syncLoading,
		cleanupLoading,
		activeDestructiveOp,
		destructiveConfirmText,
		onRefresh,
		onStartDestructiveOp,
		onCancelDestructiveOp,
		onConfirmTextChange,
		onCleanupOrphans,
		onCleanupStale,
		onPurgeAll
	}: Props = $props();

	const showPanel = $derived(
		!syncStatus.synced ||
		syncStatus.orphaned_collections.length > 0 ||
		syncStatus.missing_sources.length > 0
	);
</script>

{#if showPanel}
	<div class="panel overflow-hidden border-amber-500/15">
		<div class="panel-header flex items-center justify-between bg-amber-500/5">
			<div class="flex items-center gap-2">
				<svg class="w-4 h-4 text-amber-400/80" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
				</svg>
				<span class="text-sm text-surface-300">Sync Status: Database - Qdrant</span>
			</div>
			<button
				onclick={onRefresh}
				disabled={syncLoading}
				class="btn btn-ghost btn-sm"
			>
				{syncLoading ? 'Checking...' : 'Refresh'}
			</button>
		</div>

		<div class="p-4 space-y-4">
			<!-- Orphaned collections -->
			{#if syncStatus.orphaned_collections.length > 0}
				<div class="inner-card p-3">
					<div class="flex items-center justify-between mb-2">
						<span class="text-sm text-surface-300 flex items-center gap-2">
							<svg class="w-4 h-4 text-amber-400/70" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
								<path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
							</svg>
							Orphaned Collections ({syncStatus.orphaned_collections.length})
						</span>
						{#if activeDestructiveOp !== 'cleanup_orphans'}
							<button
								onclick={() => onStartDestructiveOp('cleanup_orphans')}
								disabled={cleanupLoading || activeDestructiveOp !== null}
								class="px-3 py-1 text-xs bg-amber-500/10 text-amber-400/80 hover:bg-amber-500/15 rounded border border-amber-500/15 disabled:opacity-50"
							>
								Cleanup Orphans
							</button>
						{/if}
					</div>
					<p class="text-xs text-surface-400 mb-2">
						Collections in Qdrant not tracked in the database:
					</p>
					<div class="flex flex-wrap gap-2">
						{#each syncStatus.orphaned_collections as collection}
							<span class="px-2 py-1 text-xs bg-surface-800/50 text-surface-300 rounded border border-surface-700/30">
								{collection}
							</span>
						{/each}
					</div>

					{#if activeDestructiveOp === 'cleanup_orphans'}
						<div class="mt-4 p-4 bg-amber-500/5 border border-amber-500/15 rounded-lg">
							<p class="text-sm text-amber-300 mb-3">This will permanently delete orphaned collections.</p>
							<div class="mb-3">
								<label class="block text-xs text-surface-500 mb-1">
									Type <span class="text-amber-400 font-semibold">confirm delete</span> to proceed:
								</label>
								<input
									type="text"
									value={destructiveConfirmText}
									oninput={(e) => onConfirmTextChange(e.currentTarget.value)}
									placeholder="confirm delete"
									class="w-full input"
								/>
							</div>
							<div class="flex gap-2">
								<button
									onclick={onCleanupOrphans}
									disabled={cleanupLoading || destructiveConfirmText.toLowerCase() !== 'confirm delete'}
									class="btn btn-danger"
								>
									{cleanupLoading ? 'Deleting...' : 'Delete Orphans'}
								</button>
								<button onclick={onCancelDestructiveOp} disabled={cleanupLoading} class="btn btn-ghost">
									Cancel
								</button>
							</div>
						</div>
					{/if}
				</div>
			{/if}

			<!-- Missing in Qdrant -->
			{#if syncStatus.missing_sources.length > 0}
				<div class="inner-card p-3">
					<div class="flex items-center justify-between mb-2">
						<span class="text-sm text-surface-300 flex items-center gap-2">
							<svg class="w-4 h-4 text-red-400/70" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
								<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
							</svg>
							Missing in Qdrant ({syncStatus.missing_sources.length})
						</span>
						{#if activeDestructiveOp !== 'cleanup_stale'}
							<button
								onclick={() => onStartDestructiveOp('cleanup_stale')}
								disabled={cleanupLoading || activeDestructiveOp !== null}
								class="px-3 py-1 text-xs bg-red-500/10 text-red-400/80 hover:bg-red-500/15 rounded border border-red-500/15 disabled:opacity-50"
							>
								Remove Stale Entries
							</button>
						{/if}
					</div>
					<p class="text-xs text-surface-400 mb-2">
						Sources in database without vectors in Qdrant:
					</p>
					<div class="flex flex-wrap gap-2">
						{#each syncStatus.missing_sources as source}
							<span class="px-2 py-1 text-xs bg-surface-800/50 text-surface-300 rounded border border-surface-700/30">
								{source}
							</span>
						{/each}
					</div>

					{#if activeDestructiveOp === 'cleanup_stale'}
						<div class="mt-4 p-4 bg-red-500/5 border border-red-500/15 rounded-lg">
							<p class="text-sm text-red-300 mb-3">This will permanently remove stale database entries.</p>
							<div class="mb-3">
								<label class="block text-xs text-surface-500 mb-1">
									Type <span class="text-red-400 font-semibold">confirm delete</span> to proceed:
								</label>
								<input
									type="text"
									value={destructiveConfirmText}
									oninput={(e) => onConfirmTextChange(e.currentTarget.value)}
									placeholder="confirm delete"
									class="w-full input"
								/>
							</div>
							<div class="flex gap-2">
								<button
									onclick={onCleanupStale}
									disabled={cleanupLoading || destructiveConfirmText.toLowerCase() !== 'confirm delete'}
									class="btn btn-danger"
								>
									{cleanupLoading ? 'Deleting...' : 'Remove Stale'}
								</button>
								<button onclick={onCancelDestructiveOp} disabled={cleanupLoading} class="btn btn-ghost">
									Cancel
								</button>
							</div>
						</div>
					{/if}
				</div>
			{/if}

			<!-- Danger zone -->
			<div class="pt-2 border-t border-surface-700/20">
				{#if activeDestructiveOp !== 'purge_all'}
					<button
						onclick={() => onStartDestructiveOp('purge_all')}
						disabled={cleanupLoading || activeDestructiveOp !== null}
						class="px-3 py-1 text-xs bg-red-900/30 hover:bg-red-900/50 text-red-400/80 rounded border border-red-500/20 disabled:opacity-50 inline-flex items-center gap-1.5"
					>
						<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
						</svg>
						Purge All Data
					</button>
					<span class="text-xs text-surface-500 ml-2">Delete everything and start fresh</span>
				{/if}

				{#if activeDestructiveOp === 'purge_all'}
					<div class="mt-2 p-4 bg-red-900/20 border border-red-500/20 rounded-lg">
						<div class="flex items-center gap-2 mb-3">
							<svg class="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
								<path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
							</svg>
							<span class="text-base font-bold text-red-400">DANGER: Purge All Data</span>
						</div>
						<p class="text-sm text-red-300 mb-3">
							This will permanently delete ALL vectors and ALL database entries. This cannot be undone!
						</p>
						<div class="mb-3">
							<label class="block text-xs text-surface-400 mb-1">
								Type <span class="text-red-400 font-semibold">confirm delete</span> to proceed:
							</label>
							<input
								type="text"
								value={destructiveConfirmText}
								oninput={(e) => onConfirmTextChange(e.currentTarget.value)}
								placeholder="confirm delete"
								class="w-full input"
							/>
						</div>
						<div class="flex gap-2">
							<button
								onclick={onPurgeAll}
								disabled={cleanupLoading || destructiveConfirmText.toLowerCase() !== 'confirm delete'}
								class="btn btn-danger"
							>
								{cleanupLoading ? 'Purging...' : 'Purge All Data'}
							</button>
							<button onclick={onCancelDestructiveOp} disabled={cleanupLoading} class="btn btn-ghost">
								Cancel
							</button>
						</div>
					</div>
				{/if}
			</div>
		</div>
	</div>
{/if}
