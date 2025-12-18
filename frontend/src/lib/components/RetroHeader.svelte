<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		path: string;
		flag?: string;
		rightContent?: Snippet;
		class?: string;
	}

	let {
		path,
		flag,
		rightContent,
		class: className = ''
	}: Props = $props();
</script>

<header class="px-6 py-4 border-b retro-border bg-surface-800/50 backdrop-blur-sm {className}">
	<div class="flex items-center justify-between">
		<div class="flex items-center gap-3">
			<span class="text-confluent-primary font-mono text-sm text-glow-blue">$</span>
			<h1 class="font-mono text-lg text-surface-100">{path}</h1>
			{#if flag}
				<span class="text-surface-500 font-mono text-sm">{flag}</span>
			{/if}
		</div>
		{#if rightContent}
			<div class="flex items-center gap-4">
				{@render rightContent()}
			</div>
		{/if}
	</div>
</header>

