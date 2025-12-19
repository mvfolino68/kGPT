<script lang="ts">
	import { executionPaths, getPathColor } from './types';
	import { Button } from '$lib/components/ui';

	interface Props {
		selectedPath: number;
		onSelect: (id: number) => void;
	}

	let { selectedPath, onSelect }: Props = $props();
</script>

<div class="flex justify-center">
	<div class="inline-flex bg-bg-elevated rounded-lg p-1 ring-1 ring-white/5 gap-1">
		{#each executionPaths as path}
			<Button
				variant={selectedPath === path.id ? 'primary' : 'ghost'}
				size="sm"
				class="px-3 {selectedPath === path.id
					? `${getPathColor(path.color, 'bg')} ${getPathColor(path.color, 'text')} ${getPathColor(path.color, 'border')} border shadow-sm`
					: 'text-text-tertiary hover:text-text hover:bg-surface-700 border border-transparent active:bg-surface-active'}"
				onclick={() => onSelect(path.id)}
				aria-pressed={selectedPath === path.id}
			>
				{path.shortName}
			</Button>
		{/each}
	</div>
</div>
