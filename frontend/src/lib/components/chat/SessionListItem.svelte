<script lang="ts">
	import { ListItem, Button, IconButton, Icon } from '$lib/components/ui';

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
			class="w-full bg-surface-700/50 border-none rounded-md px-2 py-1 text-xs text-foreground placeholder:text-muted transition-all focus:outline-none focus:bg-surface-700 focus:ring-2 focus:ring-primary-600/50"
		/>
	{:else}
		<div class="flex items-center justify-between">
			<span class="text-xs truncate flex-1">
				{isActive ? '> ' : ''}{session.title}
			</span>
			{#if isConfirmingDelete}
				<div class="flex gap-1">
					<Button variant="danger-solid" size="xs" onclick={onConfirmDelete}>
						<Icon name="trash" size="xs" strokeWidth={2} />
						delete
					</Button>
					<Button variant="default" size="xs" onclick={onCancelDelete}>
						cancel
					</Button>
				</div>
			{:else}
				<div class="flex gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
					<IconButton variant="primary" size="xs" title="Edit" onclick={onEdit}>
						<Icon name="edit" size="sm" strokeWidth={2} />
					</IconButton>
					<IconButton variant="danger" size="xs" title="Delete" onclick={onDelete}>
						<Icon name="trash" size="sm" strokeWidth={2} />
					</IconButton>
				</div>
			{/if}
		</div>
		<span class="text-[10px] text-surface-600 font-mono">{formatDate(session.updated_at)}</span>
	{/if}
</ListItem>
