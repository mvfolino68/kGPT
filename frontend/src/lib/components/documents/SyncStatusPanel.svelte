<script lang="ts">
	import { Button, Card, Icon, ConfirmDialog } from '$lib/components/ui';
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

	$effect(() => {
		// Sync logic removed as ConfirmDialog handles its own input state
		// If we need to bubble input up, we'd need to update ConfirmDialog or keep manual input
	});

	const showPanel = $derived(
		!syncStatus.synced ||
		syncStatus.orphaned_collections.length > 0 ||
		syncStatus.missing_sources.length > 0
	);
</script>

{#if showPanel}
	<Card variant="warning" title="Sync Status: Database - Qdrant">
		{#snippet actions()}
			<Button
				variant="ghost"
				size="sm"
				onclick={onRefresh}
				disabled={syncLoading}
				loading={syncLoading}
			>
				Refresh
			</Button>
		{/snippet}
		{#snippet children()}
		<div class="space-y-4">
			<!-- Orphaned collections -->
			{#if syncStatus.orphaned_collections.length > 0}
				<div class="bg-surface rounded-lg p-3">
					<div class="flex items-center justify-between mb-2">
						<span class="text-sm text-text-secondary flex items-center gap-2">
							<Icon name="trash" size="sm" class="text-warning" />
							Orphaned Collections ({syncStatus.orphaned_collections.length})
						</span>
						{#if activeDestructiveOp !== 'cleanup_orphans'}
							<Button
								variant="warning"
								size="sm"
								onclick={() => onStartDestructiveOp('cleanup_orphans')}
								disabled={cleanupLoading || activeDestructiveOp !== null}
							>
								Cleanup Orphans
							</Button>
						{/if}
					</div>
					<p class="text-xs text-text-tertiary mb-2">
						Collections in Qdrant not tracked in the database:
					</p>
					<div class="flex flex-wrap gap-2">
						{#each syncStatus.orphaned_collections as collection}
							<span class="px-2 py-1 text-xs bg-bg text-text-secondary rounded">
								{collection}
							</span>
						{/each}
					</div>

					{#if activeDestructiveOp === 'cleanup_orphans'}
						<div class="mt-4 p-4 bg-warning-bg rounded-lg">
							<ConfirmDialog
								title="Delete Orphans"
								message="This will permanently delete orphaned collections."
								confirmText="confirm delete"
								confirmLabel="Delete Orphans"
								variant="danger"
								isLoading={cleanupLoading}
								onConfirm={onCleanupOrphans}
								onCancel={onCancelDestructiveOp}
							/>
						</div>
					{/if}
				</div>
			{/if}

			<!-- Missing in Qdrant -->
			{#if syncStatus.missing_sources.length > 0}
				<div class="bg-surface rounded-lg p-3">
					<div class="flex items-center justify-between mb-2">
						<span class="text-sm text-text-secondary flex items-center gap-2">
							<Icon name="x" size="sm" class="text-error" />
							Missing in Qdrant ({syncStatus.missing_sources.length})
						</span>
						{#if activeDestructiveOp !== 'cleanup_stale'}
							<Button
								variant="danger"
								size="sm"
								onclick={() => onStartDestructiveOp('cleanup_stale')}
								disabled={cleanupLoading || activeDestructiveOp !== null}
							>
								Remove Stale Entries
							</Button>
						{/if}
					</div>
					<p class="text-xs text-text-tertiary mb-2">
						Sources in database without vectors in Qdrant:
					</p>
					<div class="flex flex-wrap gap-2">
						{#each syncStatus.missing_sources as source}
							<span class="px-2 py-1 text-xs bg-bg text-text-secondary rounded">
								{source}
							</span>
						{/each}
					</div>

					{#if activeDestructiveOp === 'cleanup_stale'}
						<div class="mt-4 p-4 bg-error-bg rounded-lg">
							<ConfirmDialog
								title="Remove Stale Entries"
								message="This will permanently remove stale database entries."
								confirmText="confirm delete"
								confirmLabel="Remove Stale"
								variant="danger"
								isLoading={cleanupLoading}
								onConfirm={onCleanupStale}
								onCancel={onCancelDestructiveOp}
							/>
						</div>
					{/if}
				</div>
			{/if}

			<!-- Danger zone -->
			<div class="pt-4 mt-2 border-t border-border-subtle">
				{#if activeDestructiveOp !== 'purge_all'}
					<Button
						variant="danger"
						size="sm"
						onclick={() => onStartDestructiveOp('purge_all')}
						disabled={cleanupLoading || activeDestructiveOp !== null}
					>
						<Icon name="warning" size="xs" />
						Purge All Data
					</Button>
					<span class="text-xs text-text-tertiary ml-2">Delete everything and start fresh</span>
				{/if}

				{#if activeDestructiveOp === 'purge_all'}
					<div class="mt-2 p-4 bg-error-bg rounded-lg">
						<ConfirmDialog
							title="DANGER: Purge All Data"
							message="This will permanently delete ALL vectors and ALL database entries. This cannot be undone!"
							confirmText="confirm delete"
							confirmLabel="Purge All Data"
							variant="danger"
							isLoading={cleanupLoading}
							onConfirm={onPurgeAll}
							onCancel={onCancelDestructiveOp}
						/>
					</div>
				{/if}
			</div>
		</div>
	{/snippet}
	</Card>
{/if}
