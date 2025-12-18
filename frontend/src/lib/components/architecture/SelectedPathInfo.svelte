<script lang="ts">
	import type { ExecutionPath } from './types';
	import { getPathColor } from './types';

	interface Props {
		path: ExecutionPath;
	}

	let { path }: Props = $props();
</script>

<div class="text-center p-4 rounded-xl {getPathColor(path.color, 'bg')} border {getPathColor(path.color, 'border')}">
	<h2 class="text-lg font-bold {getPathColor(path.color, 'text')} mb-1">
		{path.name}
	</h2>
	<p class="text-surface-300 text-sm">{path.description}</p>
	<p class="text-surface-500 text-xs mt-2 italic">{path.example}</p>
</div>
