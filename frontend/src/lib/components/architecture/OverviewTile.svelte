<script lang="ts">
	type Tone = {
		bg: string;
		text: string;
	};

	interface Props {
		title: string;
		subtitle?: string;
		description: string;
		tone: Tone;
		iconPath?: string;
		letter?: string;
	}

	let { title, subtitle, description, tone, iconPath, letter }: Props = $props();
</script>

<div class="p-4 bg-surface-700/30 rounded-xl hover:bg-surface-700/50 transition-colors">
	<div class="flex items-center gap-3 mb-3">
		<div class="w-10 h-10 rounded-lg {tone.bg} flex items-center justify-center">
			{#if iconPath}
				<svg class="w-5 h-5 {tone.text}" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d={iconPath} />
				</svg>
			{:else if letter}
				<span class="{tone.text} font-bold text-sm">{letter}</span>
			{/if}
		</div>
		<div class="min-w-0">
			<div class="text-sm font-bold {tone.text} truncate">{title}</div>
			{#if subtitle}
				<div class="text-xs text-text-tertiary truncate">{subtitle}</div>
			{/if}
		</div>
	</div>
	<p class="text-xs text-text-secondary">{description}</p>
</div>
