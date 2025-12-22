<script lang="ts">
	import type { AgentActivity } from '$lib/stores/chat';
	import { agentConfig, getTraceStatusColor, formatDuration } from './types';
	import { Button } from '$lib/components/ui';

	interface Props {
		activity: AgentActivity;
		expanded: boolean;
		onToggle: () => void;
		compact?: boolean;
	}

	let { activity, expanded, onToggle, compact = false }: Props = $props();

	const config = $derived(agentConfig[activity.agent] || agentConfig.error);
	const statusColor = $derived(getTraceStatusColor(activity.status));
	const duration = $derived(formatDuration(activity.duration_ms));
	const hasResult = $derived(!!activity.result);
</script>

<div class="rounded-lg bg-surface-800 overflow-hidden">
	<Button
		variant="ghost"
		size={compact ? 'sm' : 'md'}
		class="w-full justify-start gap-2 rounded-none {compact ? 'px-2.5 py-2' : 'px-3 py-2.5'} {hasResult ? '' : 'cursor-default pointer-events-none'}"
		disabled={!hasResult}
		onclick={() => hasResult && onToggle()}
	>
		<!-- Status indicator -->
		<div class="w-1.5 h-1.5 rounded-full {statusColor} flex-shrink-0"></div>

		<!-- Agent icon -->
		<div
			class="rounded flex items-center justify-center flex-shrink-0 {config.bg}
				{compact ? 'w-5 h-5' : 'w-6 h-6'}"
		>
			<svg
				class="{config.color} {compact ? 'w-3 h-3' : 'w-3.5 h-3.5'}"
				fill="none"
				stroke="currentColor"
				viewBox="0 0 24 24"
				stroke-width="1.5"
			>
				<path stroke-linecap="round" stroke-linejoin="round" d={config.icon} />
			</svg>
		</div>

		<!-- Label and Description -->
		<div class="flex-1 min-w-0 pr-2">
			<div class="font-medium text-surface-300 text-left
				{compact ? 'text-xs' : 'text-sm'}">
				{config.label}
			</div>
			{#if activity.description}
				<div class="text-surface-500 truncate text-left
					{compact ? 'text-[10px]' : 'text-xs'}">
					{activity.description}
				</div>
			{/if}
		</div>

		<!-- Duration -->
		{#if duration}
			<span class="text-surface-500 font-mono {compact ? 'text-[10px]' : 'text-xs'} flex-shrink-0">
				{duration}
			</span>
		{/if}

		<!-- Expand icon -->
		{#if hasResult}
			<svg
				class="text-surface-500 transition-transform {compact ? 'w-3 h-3' : 'w-4 h-4'} {expanded ? 'rotate-90' : ''}"
				fill="none"
				stroke="currentColor"
				viewBox="0 0 24 24"
				stroke-width="1.5"
			>
				<path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
			</svg>
		{/if}
	</Button>

	<!-- Expanded result -->
	{#if expanded && hasResult}
		<div class="px-2.5 pb-2 pt-1 bg-surface-700/20">
			<pre
				class="text-surface-400 overflow-x-auto whitespace-pre-wrap p-2 bg-surface-900/50 rounded break-all
					{compact ? 'text-[10px]' : 'text-xs'}">{JSON.stringify(activity.result, null, 2)}</pre>
		</div>
	{/if}
</div>
