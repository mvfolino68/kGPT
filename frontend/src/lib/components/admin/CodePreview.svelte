<script lang="ts">
	interface Props {
		code: string;
	}

	let { code }: Props = $props();
	let showCode = $state(false);
</script>

<div class="mt-3">
	<button
		type="button"
		onclick={() => showCode = !showCode}
		class="text-xs text-surface-500 hover:text-surface-300 transition-colors flex items-center gap-1"
	>
		<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
			<path stroke-linecap="round" stroke-linejoin="round" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
		</svg>
		{showCode ? 'Hide code' : 'View executed code'}
	</button>
	{#if showCode}
		<pre class="mt-2 text-xs font-mono bg-surface-800/80 rounded-lg p-3 overflow-x-auto text-surface-300 border border-surface-700/50">{code}</pre>
	{/if}
</div>

