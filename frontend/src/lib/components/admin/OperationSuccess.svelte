<script lang="ts">
	import { Card } from '$lib/components/ui';
	import type { AdminOperationResult } from './types';
	import OperationHeader from './OperationHeader.svelte';
	import { StatusIndicator } from '$lib/components';

	interface Props {
		result: AdminOperationResult;
	}

	let { result }: Props = $props();

	const data = $derived(result.data || {});
	const entries = $derived(Object.entries(data).slice(0, 10));
</script>

<Card>
	<div class="flex items-center gap-2.5 mb-3">
		<StatusIndicator status="active" size="md" pulse />
		<span class="text-sm font-semibold text-emerald-400">
			{result.operation_name || result.operation_title || result.operation || 'Operation Completed'}
		</span>
	</div>

	{#if result.message}
		<p class="text-sm text-surface-300">{result.message}</p>
	{/if}

	{#if result.topic}
		<p class="text-sm text-surface-400 mt-2">Topic: {result.topic}</p>
	{/if}

	{#if typeof result.partitions === 'number'}
		<p class="text-sm text-surface-400">Partitions: {result.partitions}</p>
	{/if}

	{#if result.replication_factor}
		<p class="text-sm text-surface-400">Replication Factor: {result.replication_factor}</p>
	{/if}

	{#if entries.length > 0}
		<div class="mt-3 space-y-1.5">
			{#each entries as [key, value]}
				<div class="flex items-center justify-between text-xs bg-surface-800/40 rounded px-2.5 py-1.5">
					<span class="text-surface-400">{key}</span>
					<span class="text-emerald-400 font-mono truncate max-w-[60%]">
						{typeof value === 'object' ? JSON.stringify(value).slice(0, 50) : value}
					</span>
				</div>
			{/each}
		</div>
	{/if}
</Card>
