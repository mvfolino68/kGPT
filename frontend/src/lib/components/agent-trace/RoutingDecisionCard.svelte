<script lang="ts">
	import { Badge } from '$lib/components/ui';
	import type { RoutingDecision } from '$lib/stores/chat';

	interface Props {
		decision: RoutingDecision;
		expanded: boolean;
		onToggle: () => void;
		compact?: boolean;
	}

	let { decision, expanded, onToggle, compact = false }: Props = $props();
</script>

<div class="pt-2 mt-2">
	<button
		type="button"
		onclick={onToggle}
		class="flex items-center gap-1.5 font-medium text-surface-500 uppercase tracking-wider mb-2 hover:text-surface-400
			{compact ? 'text-[10px]' : 'text-xs'}"
	>
		<svg
			class="transition-transform {compact ? 'w-2.5 h-2.5' : 'w-3 h-3'} {expanded ? 'rotate-90' : ''}"
			fill="none"
			stroke="currentColor"
			viewBox="0 0 24 24"
			stroke-width="2"
		>
			<path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
		</svg>
		Routing
	</button>

	{#if expanded}
		<div
			class="rounded-lg bg-surface-800 space-y-2
				{compact ? 'p-2.5' : 'p-3'}"
		>
			<div class="flex items-center justify-between">
				<span class="text-surface-500 {compact ? 'text-[10px]' : 'text-xs'}">Route</span>
				<Badge variant="primary" size={compact ? 'sm' : 'md'}>{decision.route}</Badge>
			</div>

			{#if decision.reasoning}
				<p class="text-surface-400 leading-relaxed {compact ? 'text-[11px]' : 'text-sm'}">
					{decision.reasoning}
				</p>
			{/if}

		<div class="flex flex-wrap gap-1">
			{#if decision.needs_cluster}
				<span
					class="rounded bg-blue-500/15 text-blue-400
						{compact ? 'px-1.5 py-0.5 text-[9px]' : 'px-2 py-0.5 text-xs'}"
				>
					cluster
				</span>
			{/if}
			{#if decision.needs_retrieval}
				<span
					class="rounded bg-blue-500/15 text-blue-400
						{compact ? 'px-1.5 py-0.5 text-[9px]' : 'px-2 py-0.5 text-xs'}"
				>
					retrieval
				</span>
			{/if}
			{#if decision.needs_web_search}
				<span
					class="rounded bg-green-500/15 text-green-400
						{compact ? 'px-1.5 py-0.5 text-[9px]' : 'px-2 py-0.5 text-xs'}"
				>
					web
				</span>
			{/if}
			{#if decision.needs_admin}
				<span
					class="rounded bg-amber-500/15 text-amber-400
						{compact ? 'px-1.5 py-0.5 text-[9px]' : 'px-2 py-0.5 text-xs'}"
				>
					admin
				</span>
			{/if}
		</div>
		</div>
	{/if}
</div>
