<script lang="ts">
	import { Icon } from '$lib/components/ui';
	import { sourceTypeOptions, type SourceType } from './types';

	interface Props {
		activeType: SourceType;
		onChange: (type: SourceType) => void;
	}

	let { activeType, onChange }: Props = $props();

	const getIconForType = (type: SourceType) => {
		switch (type) {
			case 'github': return 'github';
			case 'file': return 'file-text';
			case 'text': return 'align-left';
			default: return 'link';
		}
	};
</script>

<div class="border-b border-white/5 p-1">
	<div class="grid grid-cols-3 gap-1">
		{#each sourceTypeOptions as option}
			{@const isSelected = activeType === option.value}
			<button
				class="flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all duration-200
					{isSelected
						? 'bg-surface-700 text-white shadow-sm ring-1 ring-white/10'
						: 'text-surface-400 hover:text-surface-200 hover:bg-surface-800'}"
				onclick={() => onChange(option.value)}
			>
				<Icon name={getIconForType(option.value)} size="sm" />
				{option.label}
			</button>
		{/each}
	</div>
</div>
