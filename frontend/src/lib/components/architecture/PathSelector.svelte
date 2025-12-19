<script lang="ts">
	import { executionPaths, getPathColor } from './types';

	interface Props {
		selectedPath: number;
		onSelect: (id: number) => void;
	}

	let { selectedPath, onSelect }: Props = $props();
</script>

<div class="flex justify-center">
	<div class="inline-flex bg-bg-elevated rounded-lg p-1 ring-1 ring-white/5 gap-1">
		{#each executionPaths as path}
			<button
				type="button"
				onclick={() => onSelect(path.id)}
				aria-pressed={selectedPath === path.id}
				class="
					inline-flex items-center justify-center
					px-3 py-1.5 rounded-md text-xs font-medium
					transition-all duration-150 ease-out cursor-pointer
					focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:ring-offset-2 focus-visible:ring-offset-bg
					{selectedPath === path.id
						? `${getPathColor(path.color, 'bg')} ${getPathColor(path.color, 'text')} ${getPathColor(path.color, 'border')} border shadow-sm`
						: 'text-text-tertiary hover:text-text hover:bg-surface-700 border border-transparent active:bg-surface-active'}
				"
			>
				{path.shortName}
			</button>
		{/each}
	</div>
</div>
