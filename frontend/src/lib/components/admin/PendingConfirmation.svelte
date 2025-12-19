<script lang="ts">
	import { Card, Button } from '$lib/components/ui';
	import type { AdminOperationResult } from './types';
	import OperationHeader from './OperationHeader.svelte';

	interface Props {
		result: AdminOperationResult;
		isExecuting: boolean;
		executionError: string | null;
		onConfirm: () => void;
		onCancel: () => void;
	}

	let { result, isExecuting, executionError, onConfirm, onCancel }: Props = $props();

	const isHighWarning = $derived(result.warning_level === 'high');
</script>

<Card>
	<OperationHeader
		icon="warning"
		title={result.operation_title || result.operation || 'Confirm Operation'}
		subtitle="Requires confirmation"
		color={isHighWarning ? 'red' : 'amber'}
	/>

	{#if result.confirmation_message}
		<div class="mb-4 p-3 bg-surface-800/50 rounded-lg border border-surface-700/50">
			<p class="text-sm text-surface-200">{result.confirmation_message}</p>
		</div>
	{/if}

	{#if result.warning_message && isHighWarning}
		<div class="mb-4 p-3 bg-red-500/10 rounded-lg border border-red-500/30">
			<div class="flex items-start gap-2">
				<svg class="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
				</svg>
				<p class="text-sm text-red-300">{result.warning_message}</p>
			</div>
		</div>
	{/if}

	{#if result.code_preview}
		<div class="mb-4">
			<p class="text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-2">Code to execute</p>
			<pre class="text-xs font-mono bg-surface-800/80 rounded-lg p-3 overflow-x-auto text-surface-300 border border-surface-700/50">{result.code_preview}</pre>
		</div>
	{/if}

	{#if executionError}
		<div class="mb-4 p-3 bg-red-500/10 rounded-lg border border-red-500/30">
			<p class="text-sm text-red-300">{executionError}</p>
		</div>
	{/if}

	<div class="flex gap-3">
		<Button
			variant={isHighWarning ? 'danger' : 'warning'}
			size="md"
			class="flex-1"
			disabled={isExecuting}
			loading={isExecuting}
			onclick={onConfirm}
		>
			{isHighWarning ? 'Confirm Delete' : 'Confirm'}
		</Button>
		<Button
			variant="secondary"
			size="md"
			disabled={isExecuting}
			onclick={onCancel}
		>
			Cancel
		</Button>
	</div>
</Card>

