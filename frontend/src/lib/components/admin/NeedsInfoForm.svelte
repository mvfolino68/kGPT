<script lang="ts">
	import type { AdminOperationResult, InputField } from '$lib/stores/chat';
	import { executeAdminOperation } from '$lib/api';
	import { Button } from '$lib/components/ui';

	interface Props {
		result: AdminOperationResult;
		onComplete?: (result: AdminOperationResult) => void;
	}

	let { result, onComplete }: Props = $props();

	let isExecuting = $state(false);
	let executionError = $state<string | null>(null);
	let formValues = $state<Record<string, string | number>>({});

	// Initialize form values from defaults
	$effect(() => {
		if (result.input_fields) {
			const defaults: Record<string, string | number> = {};
			for (const field of result.input_fields) {
				if (field.default !== null && field.default !== undefined) {
					defaults[field.name] = field.default;
				}
			}
			formValues = defaults;
		}
	});

	async function handleSubmit() {
		if (!result.operation) return;

		isExecuting = true;
		executionError = null;

		try {
			const mergedParams = { ...(result.params || {}), ...formValues };
			const response = await executeAdminOperation({
				operation: result.operation,
				params: mergedParams
			});

			onComplete?.({ ...response, executed: true, pending: false, needs_info: false });
		} catch (error) {
			executionError = error instanceof Error ? error.message : 'Operation failed';
		} finally {
			isExecuting = false;
		}
	}

	function handleCancel() {
		onComplete?.({ success: false, error: 'Operation cancelled by user' });
	}

	function formatOperationTitle(op: string | undefined): string {
		if (!op) return 'Additional Information Required';
		return op.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
	}
</script>

<div class="bg-blue-500/10 border border-blue-500/30 rounded-xl p-5">
	<div class="flex items-center gap-2.5 mb-4">
		<div class="w-9 h-9 rounded-lg bg-blue-500/20 flex items-center justify-center border border-blue-500/30">
			<svg class="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
				<path stroke-linecap="round" stroke-linejoin="round" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
			</svg>
		</div>
		<div>
			<span class="text-sm font-bold font-mono text-blue-400">
				{result.operation_title || formatOperationTitle(result.operation)}
			</span>
			<p class="text-xs text-surface-500 font-mono">Please provide the required information</p>
		</div>
	</div>

	{#if result.message || result.guidance_message}
		<div class="mb-4 p-3 bg-surface-800/50 rounded-lg border border-surface-700/50">
			<p class="text-sm text-surface-200 font-mono">{result.message || result.guidance_message}</p>
		</div>
	{/if}

	{#if result.input_fields && result.input_fields.length > 0}
		<div class="space-y-4 mb-4">
			{#each result.input_fields as field}
				<div>
					<label for={"needs-info-" + field.name} class="block text-xs font-mono text-surface-400 mb-1.5">
						{field.label || field.name}
						{#if field.required}
							<span class="text-red-400">*</span>
						{/if}
					</label>

					{#if field.field_type === 'select' && field.options}
						<select
							id={"needs-info-" + field.name}
							class="w-full px-3 py-2 bg-surface-800/80 border border-surface-700/50 rounded-lg text-sm font-mono text-surface-200 focus:outline-none focus:border-blue-500/50"
							bind:value={formValues[field.name]}
						>
							<option value="">Select...</option>
							{#each field.options as option}
								<option value={option}>{option}</option>
							{/each}
						</select>
					{:else if field.field_type === 'number'}
						<input
							id={"needs-info-" + field.name}
							type="number"
							class="w-full px-3 py-2 bg-surface-800/80 border border-surface-700/50 rounded-lg text-sm font-mono text-surface-200 focus:outline-none focus:border-blue-500/50"
							placeholder={field.placeholder || ''}
							bind:value={formValues[field.name]}
						/>
					{:else}
						<input
							id={"needs-info-" + field.name}
							type="text"
							class="w-full px-3 py-2 bg-surface-800/80 border border-surface-700/50 rounded-lg text-sm font-mono text-surface-200 focus:outline-none focus:border-blue-500/50"
							placeholder={field.placeholder || ''}
							bind:value={formValues[field.name]}
						/>
					{/if}

					{#if field.hint}
						<p class="text-xs text-surface-500 font-mono mt-1">{field.hint}</p>
					{/if}
				</div>
			{/each}
		</div>
	{/if}

	{#if executionError}
		<div class="mb-4 p-3 bg-red-500/10 rounded-lg border border-red-500/30">
			<p class="text-sm text-red-300 font-mono">{executionError}</p>
		</div>
	{/if}

	<div class="flex gap-3">
		<Button
			variant="primary"
			size="md"
			class="flex-1 font-mono font-bold"
			disabled={isExecuting}
			loading={isExecuting}
			onclick={handleSubmit}
		>
			Submit
		</Button>
		<Button
			variant="secondary"
			size="md"
			class="font-mono"
			disabled={isExecuting}
			onclick={handleCancel}
		>
			Cancel
		</Button>
	</div>
</div>
