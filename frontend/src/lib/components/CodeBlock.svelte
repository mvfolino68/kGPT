<script lang="ts">
	interface Props {
		code: string;
		language?: string;
		class?: string;
	}

	let { code, language, class: className = '' }: Props = $props();
</script>

<div class="relative group {className}">
	<pre class="bg-surface-900 border border-white/5 rounded-xl p-4 overflow-x-auto shadow-xl"><code class="text-sm font-mono text-surface-200">{code}</code></pre>
	{#if language}
		<div class="absolute top-2 right-2 px-2 py-0.5 bg-surface-800/80 border border-white/5 rounded text-xs text-surface-500 font-mono">
			{language}
		</div>
	{/if}
</div>
