<script lang="ts">
	import type { Snippet } from 'svelte';
	import { Badge } from '$lib/components/ui';

	interface Props {
		title: string;
		icon?: Snippet;
		status?: 'saved' | 'connected' | null;
		variant?: 'default' | 'success';
		headerAction?: Snippet;
		children: Snippet;
		footer?: Snippet;
	}

	let {
		title,
		icon,
		status = null,
		variant = 'default',
		headerAction,
		children,
		footer
	}: Props = $props();

	const variantClasses = {
		default: 'border-surface-700/50',
		success: 'border-emerald-500/30'
	};

	const statusConfig = {
		saved: { variant: 'default' as const, label: 'saved' },
		connected: { variant: 'success' as const, label: 'connected' }
	};
</script>

<div class="bg-surface-900 border {variantClasses[variant]} rounded-lg overflow-hidden">
	<!-- Header -->
	<div class="px-4 py-3 border-b border-surface-700/50 flex items-center justify-between">
		<div class="flex items-center gap-2.5">
			{#if icon}
				<span class="text-surface-400">
					{@render icon()}
				</span>
			{/if}
			<span class="text-sm font-medium text-surface-200">{title}</span>
			{#if status}
				<Badge variant={statusConfig[status].variant} size="sm">
					{statusConfig[status].label}
				</Badge>
			{/if}
		</div>
		{#if headerAction}
			{@render headerAction()}
		{/if}
	</div>

	<!-- Content -->
	<div class="p-4">
		{@render children()}
	</div>

	<!-- Footer (optional) -->
	{#if footer}
		<div class="px-4 py-3 border-t border-surface-700/50 flex justify-end">
			{@render footer()}
		</div>
	{/if}
</div>
