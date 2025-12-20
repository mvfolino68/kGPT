<script lang="ts">
	import { Button, Icon, IconButton, ListItem, Badge } from '$lib/components/ui';

	interface Session {
		id: string;
		title: string;
		updated_at: string;
	}

	interface Props {
		sessions: Session[];
		currentSessionId: string | null;
		sessionsLoading: boolean;
		onSelect: (id: string) => void;
		onDelete: (id: string) => void;
		onNewChat: () => void;
	}

	let { sessions, currentSessionId, sessionsLoading, onSelect, onDelete, onNewChat }: Props = $props();

	function formatDate(dateStr: string): string {
		const date = new Date(dateStr);
		const now = new Date();
		const diff = now.getTime() - date.getTime();
		const days = Math.floor(diff / (1000 * 60 * 60 * 24));

		if (days === 0) return 'Today';
		if (days === 1) return 'Yesterday';
		if (days < 7) return `${days} days ago`;
		return date.toLocaleDateString();
	}
</script>

<div class="flex-1 overflow-y-auto">
	{#if sessionsLoading}
		<div class="flex items-center justify-center py-12">
			<svg class="w-6 h-6 text-surface-500 animate-spin" fill="none" viewBox="0 0 24 24">
				<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
				<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
			</svg>
		</div>
	{:else if sessions.length === 0}
		<div class="flex flex-col items-center justify-center h-full text-center py-8 px-4">
			<div class="w-14 h-14 rounded-2xl bg-surface-800 flex items-center justify-center mb-4">
				<svg class="w-7 h-7 text-surface-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
					<path stroke-linecap="round" stroke-linejoin="round" d="M20.25 8.511c.884.284 1.5 1.128 1.5 2.097v4.286c0 1.136-.847 2.1-1.98 2.193-.34.027-.68.052-1.02.072v3.091l-3-3c-1.354 0-2.694-.055-4.02-.163a2.115 2.115 0 01-.825-.242m9.345-8.334a2.126 2.126 0 00-.476-.095 48.64 48.64 0 00-8.048 0c-1.131.094-1.976 1.057-1.976 2.192v4.286c0 .837.46 1.58 1.155 1.951m9.345-8.334V6.637c0-1.621-1.152-3.026-2.76-3.235A48.455 48.455 0 0011.25 3c-2.115 0-4.198.137-6.24.402-1.608.209-2.76 1.614-2.76 3.235v6.226c0 1.621 1.152 3.026 2.76 3.235.577.075 1.157.14 1.74.194V21l4.155-4.155" />
				</svg>
			</div>
			<h3 class="text-lg font-semibold text-surface-300 mb-2">No Conversations</h3>
			<p class="text-sm text-surface-500 max-w-xs">
				Start a new chat to begin a conversation
			</p>
			<Button variant="primary" class="mt-4" onclick={onNewChat}>
				Start New Chat
			</Button>
		</div>
	{:else}
		<div class="p-2 space-y-1">
			{#each sessions as session (session.id)}
				{@const isActive = session.id === currentSessionId}
				<div class="group flex items-center gap-1">
					<ListItem
						variant="subtle"
						active={isActive}
						class="flex-1 min-w-0 px-3 py-3 rounded-lg"
						onclick={() => onSelect(session.id)}
					>
						<div class="flex items-center justify-between gap-2">
							<div class="min-w-0 flex-1">
								<p class="text-sm font-medium text-surface-200 truncate">{session.title}</p>
								<p class="text-xs text-surface-500 mt-0.5">{formatDate(session.updated_at)}</p>
							</div>
							{#if isActive}
								<Badge variant="primary" size="sm">Active</Badge>
							{/if}
						</div>
					</ListItem>
					<IconButton
						variant="danger"
						size="xs"
						class="mr-2 opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
						title="Delete session"
						onclick={(e) => { e.stopPropagation(); onDelete(session.id); }}
					>
						<Icon name="trash" size="sm" strokeWidth={2} />
					</IconButton>
				</div>
			{/each}
		</div>
	{/if}
</div>
