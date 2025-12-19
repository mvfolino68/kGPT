<script lang="ts">
	import type { Snippet } from 'svelte';
	import { Card, StatusPill } from '$lib/components/ui';

	interface Props {
		title: string;
		icon?: Snippet;
		status?: 'saved' | 'connected' | null;
		headerAction?: Snippet;
		children: Snippet;
		footer?: Snippet;
	}

	let {
		title,
		icon,
		status = null,
		headerAction,
		children,
		footer
	}: Props = $props();

	const statusConfig = {
		saved: { status: 'success' as const, label: 'Saved' },
		connected: { status: 'success' as const, label: 'Connected' }
	};
</script>

<Card padding="md" footer={footer}>
	{#snippet header()}
		<div class="flex items-center justify-between gap-4">
			<div class="flex items-center gap-2.5 min-w-0">
				{#if icon}
					<span class="text-text-tertiary shrink-0">
						{@render icon()}
					</span>
				{/if}
				<span class="text-sm font-medium text-text truncate">{title}</span>
				{#if status}
					<StatusPill status={statusConfig[status].status} label={statusConfig[status].label} size="sm" />
				{/if}
			</div>
			{#if headerAction}
				<div class="flex items-center gap-2 shrink-0">
					{@render headerAction()}
				</div>
			{/if}
		</div>
	{/snippet}

	{#snippet children()}
		{@render children()}
	{/snippet}
</Card>
