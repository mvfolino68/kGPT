<script lang="ts">
	import type { AgentActivity } from '$lib/stores/chat';
	import { agentConfig, getStatusColor, formatDuration } from './types';

	interface Props {
		activity: AgentActivity;
		expanded: boolean;
		onToggle: () => void;
		compact?: boolean;
	}

	let { activity, expanded, onToggle, compact = false }: Props = $props();

	const config = $derived(agentConfig[activity.agent] || agentConfig.error);
	const statusColor = $derived(getStatusColor(activity.status));
	const duration = $derived(formatDuration(activity.duration_ms));
	const hasResult = $derived(!!activity.result);
</script>

<div class="rounded-lg bg-surface-800 overflow-hidden">
	<button
		type="button"
		onclick={() => hasResult && onToggle()}
		class="w-full flex items-center gap-2 transition-colors
			{compact ? 'px-2.5 py-2' : 'px-3 py-2.5'}
			{hasResult ? 'cursor-pointer hover:bg-surface-800/50' : 'cursor-default'}"
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

		<!-- Label -->
		<span
			class="font-medium text-surface-300 flex-1 text-left
				{compact ? 'text-xs' : 'text-sm'}"
		>
			{config.label}
		</span>

		<!-- Duration -->
		{#if duration}
			<span class="text-surface-500 font-mono {compact ? 'text-[10px]' : 'text-xs'}">
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
	</button>

	<!-- Expanded result -->
	{#if expanded && hasResult}
		<div class="px-2.5 pb-2 pt-1 bg-surface-700/20">
			<pre
				class="text-surface-400 overflow-x-auto whitespace-pre-wrap p-2 bg-surface-900/50 rounded break-all
					{compact ? 'text-[10px]' : 'text-xs'}">{JSON.stringify(activity.result, null, 2)}</pre>
		</div>
	{/if}
</div>
