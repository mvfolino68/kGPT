<script lang="ts">
	import type { AgentGraphNode } from '$lib/api';
	import type { NodeInfo } from './types';
	import { getPathColor } from './types';

	interface Props {
		node: AgentGraphNode;
		info: NodeInfo | undefined;
		isActive: boolean;
		isSelected: boolean;
		pathColor: string;
		stepNumber: number;
		onToggle: () => void;
	}

	let { node, info, isActive, isSelected, pathColor, stepNumber, onToggle }: Props = $props();
</script>

<button
	type="button"
	onclick={onToggle}
	class="
		w-full max-w-md p-4 rounded-xl border
		transition-all duration-150 ease-out
		focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:ring-offset-2 focus-visible:ring-offset-bg
		{isActive
			? `${getPathColor(pathColor, 'bg')} ${getPathColor(pathColor, 'border')} shadow-lg ${getPathColor(pathColor, 'glow')}`
			: 'bg-bg-elevated border-white/5 hover:border-white/10'}
		{isSelected ? 'ring-1 ring-white/10' : ''}
	"
>
	<div class="flex items-center gap-4">
		<!-- Icon -->
		<div
			class="w-12 h-12 rounded-xl flex items-center justify-center {isActive ? getPathColor(pathColor, 'bg') : 'bg-bg-elevated'}"
		>
			<svg
				class="w-6 h-6 {isActive ? getPathColor(pathColor, 'text') : 'text-text-tertiary'}"
				fill="none"
				stroke="currentColor"
				viewBox="0 0 24 24"
				stroke-width="2"
			>
				<path stroke-linecap="round" stroke-linejoin="round" d={node.icon} />
			</svg>
		</div>

		<!-- Info -->
		<div class="flex-1 text-left">
			<div class="text-sm font-semibold {isActive ? getPathColor(pathColor, 'text') : 'text-text-secondary'}">
				{node.label}
			</div>
			<div class="text-xs text-text-tertiary mt-0.5">
				{info?.role || node.description}
			</div>
		</div>

		<!-- Step number -->
		<div
			class="w-8 h-8 rounded-full flex items-center justify-center text-sm {isActive ? `${getPathColor(pathColor, 'bg')} ${getPathColor(pathColor, 'text')}` : 'bg-bg-elevated text-text-tertiary'}"
		>
			{stepNumber}
		</div>
	</div>

	<!-- Expanded details -->
	{#if isSelected && info}
		<div class="mt-4 pt-4 border-t {isActive ? 'border-current/20' : 'border-white/5'}">
			<div class="grid grid-cols-3 gap-2">
				{#each info.details as detail}
					<div class="text-xs text-left p-2 rounded-lg {isActive ? 'bg-bg-elevated/60' : 'bg-bg-elevated'}">
						<span class="{isActive ? getPathColor(pathColor, 'text') : 'text-text-tertiary'}">*</span>
						<span class="text-text-secondary ml-1">{detail}</span>
					</div>
				{/each}
			</div>
		</div>
	{/if}
</button>
