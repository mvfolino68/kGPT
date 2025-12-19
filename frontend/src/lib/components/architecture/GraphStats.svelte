<script lang="ts">
	import { Card } from '$lib/components';

	interface Props {
		agents: number;
		edges: number;
	}

	let { agents, edges }: Props = $props();
</script>

<Card padding="md" title="Graph stats" subtitle="Quick snapshot of the orchestration graph">
	<div class="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
		<div class="text-center">
			<div class="text-primary text-lg font-bold leading-none">{agents}</div>
			<div class="text-text-tertiary mt-1">Agents</div>
		</div>
		<div class="text-center">
			<div class="text-emerald-400 text-lg font-bold leading-none">{edges}</div>
			<div class="text-text-tertiary mt-1">Connections</div>
		</div>
		<div class="text-center">
			<div class="text-violet-400 text-lg font-bold leading-none">4</div>
			<div class="text-text-tertiary mt-1">Paths</div>
		</div>
		<div class="text-center">
			<div class="text-amber-400 text-lg font-bold leading-none">12+</div>
			<div class="text-text-tertiary mt-1">Technologies</div>
		</div>
	</div>
</Card>
