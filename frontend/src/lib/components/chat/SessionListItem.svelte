<script lang="ts">
	import { ListItem, Button, IconButton } from '$lib/components/ui';

	interface Props {
		session: { id: string; title: string; updated_at: string };
		isActive: boolean;
		isEditing: boolean;
		editTitle: string;
		isConfirmingDelete: boolean;
		onSelect: () => void;
		onEdit: (event: MouseEvent) => void;
		onDelete: (event: MouseEvent) => void;
		onConfirmDelete: (event: MouseEvent) => void;
		onCancelDelete: (event: MouseEvent) => void;
		onSaveEdit: () => void;
		onEditKeydown: (event: KeyboardEvent) => void;
		onEditInput: (value: string) => void;
	}

	let {
		session,
		isActive,
		isEditing,
		editTitle = $bindable(),
		isConfirmingDelete,
		onSelect,
		onEdit,
		onDelete,
		onConfirmDelete,
		onCancelDelete,
		onSaveEdit,
		onEditKeydown,
		onEditInput
	}: Props = $props();

	function formatDate(dateStr: string): string {
		const date = new Date(dateStr);
		const now = new Date();
		const diff = now.getTime() - date.getTime();
		const days = Math.floor(diff / (1000 * 60 * 60 * 24));
		if (days === 0) return 'Today';
		if (days === 1) return 'Yesterday';
		if (days < 7) return `${days}d ago`;
		return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
	}
</script>

<ListItem
	variant="subtle"
	active={isActive}
	class="group rounded-lg mb-1 {isActive ? 'text-surface-100' : 'text-surface-300'}"
	onclick={onSelect}
>
	{#if isEditing}
		<input
			type="text"
			bind:value={editTitle}
			oninput={(e) => onEditInput(e.currentTarget.value)}
			onblur={onSaveEdit}
			onkeydown={onEditKeydown}
			class="w-full input text-xs px-2 py-1"
		/>
	{:else}
		<div class="flex items-center justify-between">
			<span class="text-xs truncate flex-1">
				{isActive ? '> ' : ''}{session.title}
			</span>
			{#if isConfirmingDelete}
				<div class="flex gap-1">
					<Button variant="danger-solid" size="xs" onclick={onConfirmDelete}>
						<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
						</svg>
						delete
					</Button>
					<Button variant="default" size="xs" onclick={onCancelDelete}>
						cancel
					</Button>
				</div>
			{:else}
				<div class="flex gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
					<IconButton variant="primary" size="xs" title="Edit" onclick={onEdit}>
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
						</svg>
					</IconButton>
					<IconButton variant="danger" size="xs" title="Delete" onclick={onDelete}>
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
						</svg>
					</IconButton>
				</div>
			{/if}
		</div>
		<span class="text-[10px] text-surface-600 font-mono">{formatDate(session.updated_at)}</span>
	{/if}
</ListItem>
