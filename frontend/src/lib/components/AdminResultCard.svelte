<script lang="ts">
	import type { AdminOperationResult, PartitionDetail } from '$lib/stores/chat';
	import { StatusIndicator } from '$lib/components';

	interface Props {
		result: AdminOperationResult;
	}

	let { result }: Props = $props();

	// Check if partitions is a list (describe_topic) or number (create_topic)
	function isPartitionDetailList(partitions: number | PartitionDetail[] | undefined): partitions is PartitionDetail[] {
		return Array.isArray(partitions);
	}

	// Format config value for display
	function formatConfigValue(value: string | { value: string; is_default: boolean; is_read_only: boolean }): string {
		if (typeof value === 'string') return value;
		return value.value;
	}

	// Check if config is default
	function isDefault(value: string | { value: string; is_default: boolean; is_read_only: boolean }): boolean {
		if (typeof value === 'string') return false;
		return value.is_default;
	}

	let showAllConfigs = $state(false);
</script>

<div class="admin-result-card">
	{#if result.operation === 'describe_topic' && result.success}
		<!-- Topic Description Card -->
		<div class="retro-card-glow-green rounded-xl p-5">
			<div class="flex items-center gap-2.5 mb-4">
				<div class="w-9 h-9 rounded-lg bg-emerald-500/20 flex items-center justify-center retro-border-green">
					<svg class="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
					</svg>
				</div>
				<div>
					<span class="text-sm font-bold font-mono text-emerald-400">Topic: {result.topic}</span>
					<p class="text-xs text-surface-500 font-mono">{result.partition_count ?? (isPartitionDetailList(result.partitions) ? result.partitions.length : result.partitions ?? 0)} partitions</p>
				</div>
			</div>

			<!-- Partitions Table -->
			{#if isPartitionDetailList(result.partitions) && result.partitions.length > 0}
				<div class="mb-4">
					<h4 class="text-xs font-bold font-mono text-surface-400 uppercase tracking-wider mb-2">Partitions</h4>
					<div class="retro-card rounded-lg overflow-hidden">
						<table class="w-full text-xs font-mono">
							<thead>
								<tr class="border-b retro-border bg-surface-900/50">
									<th class="px-3 py-2 text-left text-surface-500">Partition</th>
									<th class="px-3 py-2 text-left text-surface-500">Leader</th>
									<th class="px-3 py-2 text-left text-surface-500">Replicas</th>
									<th class="px-3 py-2 text-left text-surface-500">ISRs</th>
								</tr>
							</thead>
							<tbody>
								{#each result.partitions as partition}
									<tr class="border-b retro-border last:border-b-0 hover:bg-surface-800/60 transition-colors">
										<td class="px-3 py-2 text-emerald-400">{partition.partition}</td>
										<td class="px-3 py-2 text-surface-300">{partition.leader ?? '-'}</td>
										<td class="px-3 py-2 text-surface-300">{partition.replicas?.join(', ') || '-'}</td>
										<td class="px-3 py-2 text-surface-300">{partition.isrs?.join(', ') || '-'}</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
			{/if}

			<!-- Configuration -->
			{#if result.configuration && Object.keys(result.configuration).length > 0}
				<div>
					<h4 class="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-2">Key Configuration</h4>
					<div class="space-y-1.5">
						{#each Object.entries(result.configuration).slice(0, showAllConfigs ? undefined : 6) as [key, value]}
							<div class="flex items-center justify-between text-xs bg-surface-800/40 rounded px-2.5 py-1.5">
								<span class="text-surface-400 font-mono truncate max-w-[50%]">{key}</span>
								<span class="text-emerald-400 font-mono truncate max-w-[45%]">{formatConfigValue(value)}</span>
							</div>
						{/each}
						{#if Object.keys(result.configuration).length > 6}
							<button
								type="button"
								onclick={() => (showAllConfigs = !showAllConfigs)}
								class="text-xs text-surface-500 hover:text-surface-300 transition-colors"
							>
								{showAllConfigs ? 'Show less' : `Show ${Object.keys(result.configuration).length - 6} more...`}
							</button>
						{/if}
					</div>
				</div>
			{/if}

			<!-- All Configs (expandable) -->
			{#if result.all_configs && Object.keys(result.all_configs).length > 0 && showAllConfigs}
				<details class="mt-4">
					<summary class="text-xs text-surface-500 cursor-pointer hover:text-surface-400">
						View all {Object.keys(result.all_configs).length} configuration options
					</summary>
					<div class="mt-2 max-h-64 overflow-y-auto bg-surface-800/40 rounded-lg p-2 space-y-1">
						{#each Object.entries(result.all_configs) as [key, value]}
							<div class="flex items-center justify-between text-xs px-2 py-1 rounded {isDefault(value) ? 'opacity-60' : ''}">
								<span class="text-surface-400 font-mono truncate max-w-[55%]" title={key}>{key}</span>
								<span class="text-surface-300 font-mono truncate max-w-[40%]" title={formatConfigValue(value)}>
									{formatConfigValue(value)}
								</span>
							</div>
						{/each}
					</div>
				</details>
			{/if}
		</div>

	{:else if result.success && !result.pending && !result.needs_info && !result.unclear}
		<!-- Generic Success Card -->
		<div class="retro-card-glow-green rounded-xl p-5">
			<div class="flex items-center gap-2.5 mb-3">
				<StatusIndicator status="active" size="md" pulse />
				<span class="text-sm font-bold font-mono text-emerald-400">{result.operation_title || 'Operation Successful'}</span>
			</div>
			{#if result.message}
				<p class="text-sm text-surface-300 font-mono">{result.message}</p>
			{/if}
			{#if result.topic}
				<p class="text-sm text-surface-400 font-mono mt-2">Topic: {result.topic}</p>
			{/if}
			{#if typeof result.partitions === 'number'}
				<p class="text-sm text-surface-400 font-mono">Partitions: {result.partitions}</p>
			{/if}
			{#if result.replication_factor}
				<p class="text-sm text-surface-400 font-mono">Replication Factor: {result.replication_factor}</p>
			{/if}
		</div>

	{:else if result.error}
		<!-- Error Card -->
		<div class="retro-card-glow-amber rounded-xl p-5">
			<div class="flex items-center gap-2.5 mb-3">
				<StatusIndicator status="error" size="md" />
				<span class="text-sm font-bold font-mono text-red-400">Operation Failed</span>
			</div>
			<p class="text-sm text-red-300 font-mono">{result.error}</p>
		</div>
	{/if}
</div>

