<script lang="ts">
	import { RetroButton } from '$lib/components';
	import SessionListItem from './SessionListItem.svelte';

	interface Session {
		id: string;
		title: string;
		updated_at: string;
	}

	interface Props {
		sessions: Session[];
		sessionsLoading: boolean;
		currentSessionId: string | null;
		editingSessionId: string | null;
		editingTitle: string;
		confirmingDeleteId: string | null;
		onNewChat: () => void;
		onSelectSession: (sessionId: string) => void;
		onStartEdit: (sessionId: string, title: string, event: MouseEvent) => void;
		onSaveEdit: () => void;
		onEditKeydown: (event: KeyboardEvent) => void;
		onEditInput: (value: string) => void;
		onDeleteClick: (sessionId: string, event: MouseEvent) => void;
		onConfirmDelete: (sessionId: string, event: MouseEvent) => void;
		onCancelDelete: (event: MouseEvent) => void;
	}

	let {
		sessions,
		sessionsLoading,
		currentSessionId,
		editingSessionId,
		editingTitle = $bindable(),
		confirmingDeleteId,
		onNewChat,
		onSelectSession,
		onStartEdit,
		onSaveEdit,
		onEditKeydown,
		onEditInput,
		onDeleteClick,
		onConfirmDelete,
		onCancelDelete
	}: Props = $props();
</script>

<aside class="w-64 bg-surface-900/70 border-r retro-border flex flex-col backdrop-blur-sm">
	<div class="p-4 border-b retro-border flex items-center justify-between">
		<span class="text-xs font-bold font-mono text-surface-400 uppercase tracking-wider">Sessions</span>
		<RetroButton size="sm" variant="primary" onclick={onNewChat}>
			<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
				<path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
			</svg>
		</RetroButton>
	</div>

	<div class="flex-1 overflow-y-auto py-2 px-2">
		{#if sessionsLoading}
			<div class="px-3 py-2 text-surface-500 text-xs font-mono">Loading...</div>
		{:else if sessions.length === 0}
			<div class="px-3 py-2 text-surface-600 text-xs font-mono">No sessions yet</div>
		{:else}
			{#each sessions as session (session.id)}
				<SessionListItem
					{session}
					isActive={session.id === currentSessionId}
					isEditing={editingSessionId === session.id}
					bind:editTitle={editingTitle}
					isConfirmingDelete={confirmingDeleteId === session.id}
					onSelect={() => onSelectSession(session.id)}
					onEdit={(e) => onStartEdit(session.id, session.title, e)}
					onDelete={(e) => onDeleteClick(session.id, e)}
					onConfirmDelete={(e) => onConfirmDelete(session.id, e)}
					onCancelDelete={onCancelDelete}
					onSaveEdit={onSaveEdit}
					onEditKeydown={onEditKeydown}
					onEditInput={onEditInput}
				/>
			{/each}
		{/if}
	</div>
</aside>
