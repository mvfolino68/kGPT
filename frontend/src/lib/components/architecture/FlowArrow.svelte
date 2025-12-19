<script lang="ts">
	import { getPathColor } from './types';

	interface Props {
		pathColor: string;
		isActive?: boolean;
	}

	let { pathColor, isActive = true }: Props = $props();
</script>

<div class="flex flex-col items-center">
	<div class="w-0.5 h-6 {isActive ? getPathColor(pathColor, 'bg') : 'bg-surface-700'}"></div>
	<svg
		class="w-3 h-3 -mt-1 {isActive ? getPathColor(pathColor, 'text') : 'text-surface-700'}"
		fill="currentColor"
		viewBox="0 0 12 12"
	>
		<path d="M6 9L1 4h10L6 9z" />
	</svg>
</div>

