<script lang="ts">
	import { executionPaths, getPathColor } from './types';

	interface Props {
		selectedPath: number;
		onSelect: (id: number) => void;
	}

	let { selectedPath, onSelect }: Props = $props();
</script>

<div class="flex justify-center">
	<div class="inline-flex bg-surface-800/50 border border-surface-700/50 rounded-xl p-1.5 gap-1">
		{#each executionPaths as path}
			<button
				type="button"
				onclick={() => onSelect(path.id)}
				class="px-4 py-2.5 rounded-lg text-sm transition-all duration-200 {selectedPath === path.id
					? `${getPathColor(path.color, 'bg')} ${getPathColor(path.color, 'text')} ${getPathColor(path.color, 'border')} border shadow-lg ${getPathColor(path.color, 'glow')}`
					: 'text-surface-400 hover:text-surface-200 hover:bg-surface-800 border border-transparent'}"
			>
				{path.shortName}
			</button>
		{/each}
	</div>
</div>
