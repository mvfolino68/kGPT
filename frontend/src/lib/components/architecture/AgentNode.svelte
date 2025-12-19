<script lang="ts">
	import type { AgentGraphNode } from '$lib/api';
	import type { NodeInfo } from './types';
	import { getPathColor } from './types';
	import { CardButton } from '$lib/components/ui';
	import PathTint from './PathTint.svelte';

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

<CardButton
	variant={isActive ? 'active' : 'default'}
	size="lg"
	selected={isSelected}
	class="max-w-md relative overflow-hidden {isActive
		? `${getPathColor(pathColor, 'border')} ${getPathColor(pathColor, 'glow')}`
		: ''}"
	onclick={onToggle}
>
	{#if isActive}
		<!-- Subtle tint overlay (avoid “filled” look; consistent across paths) -->
		<PathTint color={pathColor} opacity={0.10} roundedClass="rounded-xl" />
	{/if}

	<div class="relative flex items-center gap-4">
		<!-- Icon -->
		<div
			class="w-12 h-12 rounded-xl flex items-center justify-center bg-bg-elevated border {isActive ? getPathColor(pathColor, 'border') : 'border-white/5'}"
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
			class="w-8 h-8 rounded-full flex items-center justify-center text-sm bg-bg-elevated border {isActive ? `${getPathColor(pathColor, 'border')} ${getPathColor(pathColor, 'text')}` : 'border-white/5 text-text-tertiary'}"
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
</CardButton>
