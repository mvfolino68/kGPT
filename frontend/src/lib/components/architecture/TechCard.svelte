<script lang="ts">
	interface Props {
		name: string;
		description: string;
		color: string;
		icon?: string;
		letter?: string;
	}

	let { name, description, color, icon, letter }: Props = $props();
</script>

<div class="p-3 bg-surface-800 rounded-lg hover:bg-surface-700/80 transition-colors group">
	<div class="flex items-center gap-2 mb-2">
		<div class="w-8 h-8 rounded-lg bg-{color}-500/10 flex items-center justify-center">
			{#if icon}
				<svg class="w-4 h-4 text-{color}-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d={icon} />
				</svg>
			{:else if letter}
				<span class="text-{color}-400 font-bold text-sm">{letter}</span>
			{/if}
		</div>
		<span class="text-sm text-{color}-400">{name}</span>
	</div>
	<p class="text-xs text-surface-400">{description}</p>
</div>
