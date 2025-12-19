<script lang="ts">
	interface Props {
		agents: number;
		edges: number;
	}

	let { agents, edges }: Props = $props();
</script>

<div class="px-6 py-4 bg-surface-800">
	<div class="flex items-center justify-center gap-8 text-xs">
		<div class="text-center">
			<div class="text-primary-light text-lg font-bold">{agents}</div>
			<div class="text-surface-500">Agents</div>
		</div>
		<div class="text-center">
			<div class="text-emerald-400 text-lg font-bold">{edges}</div>
			<div class="text-surface-500">Connections</div>
		</div>
		<div class="text-center">
			<div class="text-violet-400 text-lg font-bold">4</div>
			<div class="text-surface-500">Paths</div>
		</div>
		<div class="text-center">
			<div class="text-amber-400 text-lg font-bold">12+</div>
			<div class="text-surface-500">Technologies</div>
		</div>
	</div>
</div>
