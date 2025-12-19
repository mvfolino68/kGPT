<script lang="ts">
	import { onMount } from 'svelte';
	import { Button } from '$lib/components/ui';
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

	const STORAGE_KEY = 'chat-sidebar-width';
	const MIN_WIDTH = 200;
	const MAX_WIDTH = 600;
	const DEFAULT_WIDTH = 256;

	let sidebarWidth = $state(DEFAULT_WIDTH);
	let isResizing = $state(false);
	let resizeHandle: HTMLButtonElement;

	onMount(() => {
		const savedWidth = localStorage.getItem(STORAGE_KEY);
		if (savedWidth) {
			const width = parseInt(savedWidth, 10);
			if (width >= MIN_WIDTH && width <= MAX_WIDTH) {
				sidebarWidth = width;
			}
		}
	});

	function handleMouseDown(e: MouseEvent) {
		e.preventDefault();
		isResizing = true;
		document.body.style.cursor = 'col-resize';
		document.body.style.userSelect = 'none';

		function handleMouseMove(e: MouseEvent) {
			if (!isResizing) return;
			const newWidth = e.clientX;
			if (newWidth >= MIN_WIDTH && newWidth <= MAX_WIDTH) {
				sidebarWidth = newWidth;
				localStorage.setItem(STORAGE_KEY, newWidth.toString());
			}
		}

		function handleMouseUp() {
			isResizing = false;
			document.body.style.cursor = '';
			document.body.style.userSelect = '';
			document.removeEventListener('mousemove', handleMouseMove);
			document.removeEventListener('mouseup', handleMouseUp);
		}

		document.addEventListener('mousemove', handleMouseMove);
		document.addEventListener('mouseup', handleMouseUp);
	}
</script>

<aside
	class="bg-surface-900 flex flex-col relative"
	style="width: {sidebarWidth}px; min-width: {MIN_WIDTH}px; max-width: {MAX_WIDTH}px;"
>
	<div class="p-4 flex items-center justify-between">
		<span class="text-[10px] font-bold text-surface-500 uppercase tracking-wider">Sessions</span>
		<Button variant="primary" size="icon" onclick={onNewChat}>
			<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
				<path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
			</svg>
		</Button>
	</div>

	<div class="flex-1 overflow-y-auto py-2 px-2">
		{#if sessionsLoading}
			<div class="px-3 py-2 text-surface-500 text-xs">Loading...</div>
		{:else if sessions.length === 0}
			<div class="px-3 py-2 text-surface-600 text-xs">No sessions yet</div>
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

	<!-- Resize Handle -->
	<button
		type="button"
		bind:this={resizeHandle}
		onmousedown={handleMouseDown}
		class="absolute top-0 right-0 w-1 h-full cursor-col-resize hover:bg-primary/50 transition-colors group"
		aria-label="Resize sidebar"
	>
		<div class="absolute top-1/2 right-0 transform -translate-y-1/2 translate-x-1/2 w-1 h-8 bg-surface-600 group-hover:bg-primary-light rounded-full opacity-0 group-hover:opacity-100 transition-opacity"></div>
	</button>
</aside>
