<script lang="ts">
	import { executionPaths, getPathColor } from './types';
	import { Button } from '$lib/components/ui';
	import PathTint from './PathTint.svelte';

	interface Props {
		selectedPath: number;
		onSelect: (id: number) => void;
	}

	let { selectedPath, onSelect }: Props = $props();
</script>

<div class="flex justify-center">
	<div class="inline-flex bg-bg-elevated rounded-lg p-1 ring-1 ring-white/5 gap-1">
		{#each executionPaths as path}
			{@const isSelected = selectedPath === path.id}
			<Button
				variant="ghost"
				size="sm"
				class="px-3 relative overflow-hidden {isSelected
					? `${getPathColor(path.color, 'border')} border-2 border-solid ${getPathColor(path.color, 'glow')} shadow-lg`
					: 'border border-transparent'}"
				onclick={() => onSelect(path.id)}
				aria-pressed={isSelected}
			>
				{#if isSelected}
					<PathTint color={path.color} opacity={0.30} roundedClass="rounded-md" />
					<span class="relative z-10 font-semibold {getPathColor(path.color, 'text')}">
						{path.shortName}
					</span>
				{:else}
					<span class="text-text-tertiary">{path.shortName}</span>
				{/if}
			</Button>
		{/each}
	</div>
</div>
