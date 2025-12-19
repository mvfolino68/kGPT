<script lang="ts">
	import type { ExecutionPath } from './types';
	import { Card } from '$lib/components';
	import { getPathColor } from './types';

	interface Props {
		path: ExecutionPath;
	}

	let { path }: Props = $props();
</script>

<Card
	class="text-center {getPathColor(path.color, 'bg')} border {getPathColor(path.color, 'border')}"
	padding="md"
>
	<h2 class="text-lg font-semibold {getPathColor(path.color, 'text')} mb-1">
		{path.name}
	</h2>
	<p class="text-text-secondary text-sm">{path.description}</p>
	<p class="text-text-tertiary text-xs mt-2 italic">{path.example}</p>
</Card>
