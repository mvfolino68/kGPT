<script lang="ts">
	import type { AdminOperationResult } from '$lib/stores/chat';

	interface Props {
		result: AdminOperationResult;
	}

	let { result }: Props = $props();
</script>

<div class="bg-amber-500/10 border border-amber-500/30 rounded-xl p-5">
	<div class="flex items-center gap-2.5 mb-3">
		<div class="w-9 h-9 rounded-lg bg-amber-500/20 flex items-center justify-center border border-amber-500/30">
			<svg class="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
				<path stroke-linecap="round" stroke-linejoin="round" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
			</svg>
		</div>
		<span class="text-sm font-bold font-mono text-amber-400">Clarification Needed</span>
	</div>

	{#if result.message || result.guidance_message}
		<p class="text-sm text-surface-300 font-mono">{result.message || result.guidance_message}</p>
	{:else}
		<p class="text-sm text-surface-300 font-mono">Could you please clarify what operation you'd like to perform?</p>
	{/if}

	{#if result.available_operations && result.available_operations.length > 0}
		<div class="mt-4">
			<p class="text-xs text-surface-500 font-mono mb-2">Available operations:</p>
			<div class="flex flex-wrap gap-2">
				{#each result.available_operations as op}
					<span class="px-2 py-1 bg-surface-800/60 rounded text-xs font-mono text-surface-300 border border-surface-700/50">
						{op.label}
					</span>
				{/each}
			</div>
		</div>
	{/if}
</div>

