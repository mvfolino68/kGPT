<script lang="ts">
	interface Props {
		name: string;
		description: string;
		color:
			| 'emerald'
			| 'orange'
			| 'blue'
			| 'violet'
			| 'red'
			| 'cyan'
			| 'amber'
			| 'sky'
			| 'teal';
		icon?: string;
		letter?: string;
	}

	let { name, description, color, icon, letter }: Props = $props();

	const toneByColor: Record<Props['color'], { bg: string; text: string }> = {
		emerald: { bg: 'bg-emerald-500/10', text: 'text-emerald-400' },
		orange: { bg: 'bg-orange-500/10', text: 'text-orange-400' },
		blue: { bg: 'bg-blue-500/10', text: 'text-blue-400' },
		violet: { bg: 'bg-violet-500/10', text: 'text-violet-400' },
		red: { bg: 'bg-red-500/10', text: 'text-red-400' },
		cyan: { bg: 'bg-cyan-500/10', text: 'text-cyan-400' },
		amber: { bg: 'bg-amber-500/10', text: 'text-amber-400' },
		sky: { bg: 'bg-sky-500/10', text: 'text-sky-400' },
		teal: { bg: 'bg-teal-500/10', text: 'text-teal-400' }
	};

	const tone = $derived(toneByColor[color]);
</script>

<div class="p-3 bg-surface-800 rounded-lg hover:bg-surface-700/80 transition-colors group">
	<div class="flex items-center gap-2 mb-2">
		<div class="w-8 h-8 rounded-lg {tone.bg} flex items-center justify-center">
			{#if icon}
				<svg class="w-4 h-4 {tone.text}" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d={icon} />
				</svg>
			{:else if letter}
				<span class="{tone.text} font-bold text-sm">{letter}</span>
			{/if}
		</div>
		<span class="text-sm {tone.text}">{name}</span>
	</div>
	<p class="text-xs text-text-secondary">{description}</p>
</div>
