<script lang="ts">
	import type { AdminOperationResult, PartitionDetail } from '$lib/stores/chat';
	import { StatusIndicator } from '$lib/components';
	import { executeAdminOperation } from '$lib/api';

	interface Props {
		result: AdminOperationResult;
		onOperationComplete?: (result: AdminOperationResult) => void;
	}

	let { result, onOperationComplete }: Props = $props();

	// State for confirmation flow
	let isExecuting = $state(false);
	let executionError = $state<string | null>(null);
	let executionResult = $state<AdminOperationResult | null>(null);

	async function handleConfirm() {
		if (!result.operation || !result.params) return;

		isExecuting = true;
		executionError = null;

		try {
			const response = await executeAdminOperation({
				operation: result.operation,
				params: result.params as Record<string, unknown>
			});

			executionResult = {
				...response,
				executed: true,
				pending: false
			};

			if (onOperationComplete) {
				onOperationComplete(executionResult);
			}
		} catch (error) {
			executionError = error instanceof Error ? error.message : 'Operation failed';
		} finally {
			isExecuting = false;
		}
	}

	function handleCancel() {
		// Just close/dismiss - the parent component can handle this
		if (onOperationComplete) {
			onOperationComplete({
				success: false,
				error: 'Operation cancelled by user'
			});
		}
	}

	// Use execution result if available, otherwise use the original result
	const displayResult = $derived(executionResult || result);

	// Check if partitions is a list (describe_topic) or number (create_topic)
	function isPartitionDetailList(
		partitions: number | PartitionDetail[] | undefined
	): partitions is PartitionDetail[] {
		return Array.isArray(partitions);
	}

	// Format config value for display
	function formatConfigValue(
		value: string | { value: string; is_default: boolean; is_read_only: boolean }
	): string {
		if (typeof value === 'string') return value;
		return value.value;
	}

	// Check if config is default
	function isDefault(
		value: string | { value: string; is_default: boolean; is_read_only: boolean }
	): boolean {
		if (typeof value === 'string') return false;
		return value.is_default;
	}

	let showAllConfigs = $state(false);
	let showCode = $state(false);

	// Get data from the new format or legacy format
	const data = $derived(displayResult.data || {});
	const topics = $derived(data.topics || []);
	const groups = $derived(data.groups || []);
	const brokers = $derived(data.brokers || []);
	const offsets = $derived(data.offsets || []);

	// Combined partition data (from new data format or legacy result format)
	const partitions = $derived(data.partitions || displayResult.partitions);

	// Combined config data
	const config = $derived(data.configuration || displayResult.configuration || {});

	// Check if this is a pending operation that needs confirmation
	const isPending = $derived(result.pending && !executionResult);

	// Check if this operation needs more information from user
	const needsInfo = $derived(result.needs_info && !executionResult);

	// Check if the operation was unclear
	const isUnclear = $derived(result.unclear && !executionResult);

	// State for needs_info form
	let formValues = $state<Record<string, string | number>>({});

	// Initialize form values from defaults when input_fields change
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

	async function handleSubmitForm() {
		if (!result.operation) return;

		isExecuting = true;
		executionError = null;

		try {
			// Merge existing params with form values
			const mergedParams = {
				...(result.params || {}),
				...formValues
			};

			const response = await executeAdminOperation({
				operation: result.operation,
				params: mergedParams
			});

			executionResult = {
				...response,
				executed: true,
				pending: false,
				needs_info: false
			};

			if (onOperationComplete) {
				onOperationComplete(executionResult);
			}
		} catch (error) {
			executionError = error instanceof Error ? error.message : 'Operation failed';
		} finally {
			isExecuting = false;
		}
	}
</script>

<div class="admin-result-card">
	<!-- ================================================================ -->
	<!-- Pending Confirmation UI -->
	<!-- ================================================================ -->
	{#if isPending}
		<div class="retro-card-glow-amber rounded-xl p-5">
			<div class="flex items-center gap-2.5 mb-4">
				<div
					class="w-9 h-9 rounded-lg flex items-center justify-center retro-border-amber {result.warning_level === 'high' ? 'bg-red-500/20' : 'bg-amber-500/20'}"
				>
					<svg
						class="w-5 h-5 {result.warning_level === 'high' ? 'text-red-400' : 'text-amber-400'}"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
						stroke-width="2"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
						/>
					</svg>
				</div>
				<div>
					<span class="text-sm font-bold font-mono {result.warning_level === 'high' ? 'text-red-400' : 'text-amber-400'}">
						{result.operation_title || result.operation || 'Confirm Operation'}
					</span>
					<p class="text-xs text-surface-500 font-mono">Requires confirmation</p>
				</div>
			</div>

			<!-- Confirmation message -->
			{#if result.confirmation_message}
				<div class="mb-4 p-3 bg-surface-800/50 rounded-lg border border-surface-700/50">
					<p class="text-sm text-surface-200 font-mono">{result.confirmation_message}</p>
				</div>
			{/if}

			<!-- Warning for destructive operations -->
			{#if result.warning_message && result.warning_level === 'high'}
				<div class="mb-4 p-3 bg-red-500/10 rounded-lg border border-red-500/30">
					<div class="flex items-start gap-2">
						<svg class="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
						</svg>
						<p class="text-sm text-red-300 font-mono">{result.warning_message}</p>
					</div>
				</div>
			{/if}

			<!-- Code preview -->
			{#if result.code_preview}
				<div class="mb-4">
					<p class="text-xs text-surface-500 font-mono mb-2">Code that will be executed:</p>
					<pre class="text-xs font-mono bg-surface-900/80 rounded-lg p-3 overflow-x-auto text-surface-300 border border-surface-800">{result.code_preview}</pre>
				</div>
			{/if}

			<!-- Execution error -->
			{#if executionError}
				<div class="mb-4 p-3 bg-red-500/10 rounded-lg border border-red-500/30">
					<p class="text-sm text-red-300 font-mono">{executionError}</p>
				</div>
			{/if}

			<!-- Action buttons -->
			<div class="flex gap-3">
				<button
					type="button"
					disabled={isExecuting}
					onclick={handleConfirm}
					class="flex-1 px-4 py-2 rounded-lg font-mono text-sm font-bold transition-all
						{result.warning_level === 'high'
							? 'bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500/30'
							: 'bg-amber-500/20 text-amber-400 border border-amber-500/30 hover:bg-amber-500/30'}
						disabled:opacity-50 disabled:cursor-not-allowed"
				>
					{#if isExecuting}
						<span class="flex items-center justify-center gap-2">
							<svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
								<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
								<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
							</svg>
							Executing...
						</span>
					{:else}
						{result.warning_level === 'high' ? 'Confirm Delete' : 'Confirm'}
					{/if}
				</button>
				<button
					type="button"
					disabled={isExecuting}
					onclick={handleCancel}
					class="px-4 py-2 rounded-lg font-mono text-sm text-surface-400 border border-surface-700/50 hover:bg-surface-800/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
				>
					Cancel
				</button>
			</div>
		</div>

	<!-- ================================================================ -->
	<!-- List Topics Result -->
	<!-- ================================================================ -->
	{:else if displayResult.operation === 'list_topics' && (displayResult.success || displayResult.executed)}
		<div class="retro-card-glow-green rounded-xl p-5">
			<div class="flex items-center gap-2.5 mb-4">
				<div
					class="w-9 h-9 rounded-lg bg-emerald-500/20 flex items-center justify-center retro-border-green"
				>
					<svg
						class="w-5 h-5 text-emerald-400"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
						stroke-width="2"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M4 6h16M4 10h16M4 14h16M4 18h16"
						/>
					</svg>
				</div>
				<div>
					<span class="text-sm font-bold font-mono text-emerald-400">Topics</span>
					<p class="text-xs text-surface-500 font-mono">{data.total_count || topics.length} total</p>
				</div>
			</div>

			{#if topics.length > 0}
				<div class="retro-card rounded-lg overflow-hidden">
					<table class="w-full text-xs font-mono">
						<thead>
							<tr class="border-b retro-border bg-surface-900/50">
								<th class="px-3 py-2 text-left text-surface-500">Topic Name</th>
								<th class="px-3 py-2 text-right text-surface-500">Partitions</th>
							</tr>
						</thead>
						<tbody>
							{#each topics.slice(0, 20) as topic}
								<tr
									class="border-b retro-border last:border-b-0 hover:bg-surface-800/60 transition-colors"
								>
									<td class="px-3 py-2 text-emerald-400"
										>{typeof topic === 'string' ? topic : topic.name}</td
									>
									<td class="px-3 py-2 text-right text-surface-300"
										>{typeof topic === 'object' ? topic.partitions : '-'}</td
									>
								</tr>
							{/each}
						</tbody>
					</table>
					{#if topics.length > 20}
						<div class="px-3 py-2 text-xs text-surface-500 bg-surface-900/30">
							... and {topics.length - 20} more topics
						</div>
					{/if}
				</div>
			{:else}
				<p class="text-sm text-surface-400 font-mono">No topics found in the cluster.</p>
			{/if}
		</div>

		<!-- ================================================================ -->
		<!-- Describe Topic Result -->
		<!-- ================================================================ -->
	{:else if displayResult.operation === 'describe_topic' && (displayResult.success || displayResult.executed)}
		<div class="retro-card-glow-green rounded-xl p-5">
			<div class="flex items-center gap-2.5 mb-4">
				<div
					class="w-9 h-9 rounded-lg bg-emerald-500/20 flex items-center justify-center retro-border-green"
				>
					<svg
						class="w-5 h-5 text-emerald-400"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
						stroke-width="2"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
						/>
					</svg>
				</div>
				<div>
					<span class="text-sm font-bold font-mono text-emerald-400"
						>Topic: {data.topic || displayResult.topic}</span
					>
					<p class="text-xs text-surface-500 font-mono">
						{data.partition_count ||
							displayResult.partition_count ||
							(isPartitionDetailList(displayResult.partitions)
								? displayResult.partitions.length
								: (displayResult.partitions ?? 0))} partitions,
						RF: {data.replication_factor || displayResult.replication_factor || '?'}
					</p>
				</div>
			</div>

			<!-- Partitions Table -->
			{#if isPartitionDetailList(partitions) && partitions.length > 0}
				<div class="mb-4">
					<h4 class="text-xs font-bold font-mono text-surface-400 uppercase tracking-wider mb-2">
						Partitions
					</h4>
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
								{#each partitions as partition}
									<tr
										class="border-b retro-border last:border-b-0 hover:bg-surface-800/60 transition-colors"
									>
										<td class="px-3 py-2 text-emerald-400">{partition.partition}</td>
										<td class="px-3 py-2 text-surface-300">{partition.leader ?? '-'}</td>
										<td class="px-3 py-2 text-surface-300">{partition.replicas?.join(', ') || '-'}</td
										>
										<td class="px-3 py-2 text-surface-300">{partition.isrs?.join(', ') || '-'}</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
			{/if}

			<!-- Configuration -->
			{#if config && Object.keys(config).length > 0}
				<div>
					<h4 class="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-2">
						Key Configuration
					</h4>
					<div class="space-y-1.5">
						{#each Object.entries(config).slice(0, showAllConfigs ? undefined : 6) as [key, value]}
							<div
								class="flex items-center justify-between text-xs bg-surface-800/40 rounded px-2.5 py-1.5"
							>
								<span class="text-surface-400 font-mono truncate max-w-[50%]">{key}</span>
								<span class="text-emerald-400 font-mono truncate max-w-[45%]"
									>{formatConfigValue(value)}</span
								>
							</div>
						{/each}
						{#if Object.keys(config).length > 6}
							<button
								type="button"
								onclick={() => (showAllConfigs = !showAllConfigs)}
								class="text-xs text-surface-500 hover:text-surface-300 transition-colors"
							>
								{showAllConfigs
									? 'Show less'
									: `Show ${Object.keys(config).length - 6} more...`}
							</button>
						{/if}
					</div>
				</div>
			{/if}
		</div>

		<!-- ================================================================ -->
		<!-- List Consumer Groups Result -->
		<!-- ================================================================ -->
	{:else if displayResult.operation === 'list_consumer_groups' && (displayResult.success || displayResult.executed)}
		<div class="retro-card-glow-green rounded-xl p-5">
			<div class="flex items-center gap-2.5 mb-4">
				<div
					class="w-9 h-9 rounded-lg bg-cyan-500/20 flex items-center justify-center retro-border-cyan"
				>
					<svg
						class="w-5 h-5 text-cyan-400"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
						stroke-width="2"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
						/>
					</svg>
				</div>
				<div>
					<span class="text-sm font-bold font-mono text-cyan-400">Consumer Groups</span>
					<p class="text-xs text-surface-500 font-mono">{data.total_count || groups.length} total</p>
				</div>
			</div>

			{#if groups.length > 0}
				<div class="retro-card rounded-lg overflow-hidden">
					<table class="w-full text-xs font-mono">
						<thead>
							<tr class="border-b retro-border bg-surface-900/50">
								<th class="px-3 py-2 text-left text-surface-500">Group ID</th>
								<th class="px-3 py-2 text-right text-surface-500">State</th>
							</tr>
						</thead>
						<tbody>
							{#each groups.slice(0, 20) as group}
								<tr
									class="border-b retro-border last:border-b-0 hover:bg-surface-800/60 transition-colors"
								>
									<td class="px-3 py-2 text-cyan-400"
										>{typeof group === 'string' ? group : group.group_id}</td
									>
									<td class="px-3 py-2 text-right text-surface-300"
										>{typeof group === 'object' ? group.state : '-'}</td
									>
								</tr>
							{/each}
						</tbody>
					</table>
					{#if groups.length > 20}
						<div class="px-3 py-2 text-xs text-surface-500 bg-surface-900/30">
							... and {groups.length - 20} more groups
						</div>
					{/if}
				</div>
			{:else}
				<p class="text-sm text-surface-400 font-mono">No consumer groups found.</p>
			{/if}
		</div>

		<!-- ================================================================ -->
		<!-- Describe Cluster Result -->
		<!-- ================================================================ -->
	{:else if displayResult.operation === 'describe_cluster' && (displayResult.success || displayResult.executed)}
		<div class="retro-card-glow-green rounded-xl p-5">
			<div class="flex items-center gap-2.5 mb-4">
				<div
					class="w-9 h-9 rounded-lg bg-violet-500/20 flex items-center justify-center retro-border-violet"
				>
					<svg
						class="w-5 h-5 text-violet-400"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
						stroke-width="2"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01"
						/>
					</svg>
				</div>
				<div>
					<span class="text-sm font-bold font-mono text-violet-400">Cluster Overview</span>
					<p class="text-xs text-surface-500 font-mono">
						{data.broker_count || 0} brokers, {data.topic_count || 0} topics
					</p>
				</div>
			</div>

			<div class="space-y-3">
				<div class="flex items-center justify-between text-xs bg-surface-800/40 rounded px-3 py-2">
					<span class="text-surface-400 font-mono">Cluster ID</span>
					<span class="text-violet-400 font-mono">{data.cluster_id || 'N/A'}</span>
				</div>
				<div class="flex items-center justify-between text-xs bg-surface-800/40 rounded px-3 py-2">
					<span class="text-surface-400 font-mono">Controller</span>
					<span class="text-violet-400 font-mono">Broker {data.controller_id ?? 'N/A'}</span>
				</div>

				{#if brokers.length > 0}
					<h4 class="text-xs font-bold font-mono text-surface-400 uppercase tracking-wider mt-4">
						Brokers
					</h4>
					<div class="retro-card rounded-lg overflow-hidden">
						<table class="w-full text-xs font-mono">
							<thead>
								<tr class="border-b retro-border bg-surface-900/50">
									<th class="px-3 py-2 text-left text-surface-500">ID</th>
									<th class="px-3 py-2 text-left text-surface-500">Host</th>
									<th class="px-3 py-2 text-right text-surface-500">Port</th>
								</tr>
							</thead>
							<tbody>
								{#each brokers as broker}
									<tr
										class="border-b retro-border last:border-b-0 hover:bg-surface-800/60 transition-colors"
									>
										<td class="px-3 py-2 text-violet-400">{broker.id}</td>
										<td class="px-3 py-2 text-surface-300">{broker.host}</td>
										<td class="px-3 py-2 text-right text-surface-300">{broker.port}</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				{/if}
			</div>
		</div>

		<!-- ================================================================ -->
		<!-- Describe Consumer Group Result -->
		<!-- ================================================================ -->
	{:else if displayResult.operation === 'describe_consumer_group' && (displayResult.success || displayResult.executed)}
		<div class="retro-card-glow-green rounded-xl p-5">
			<div class="flex items-center gap-2.5 mb-4">
				<div
					class="w-9 h-9 rounded-lg bg-cyan-500/20 flex items-center justify-center retro-border-cyan"
				>
					<svg
						class="w-5 h-5 text-cyan-400"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
						stroke-width="2"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
						/>
					</svg>
				</div>
				<div>
					<span class="text-sm font-bold font-mono text-cyan-400"
						>Group: {data.group_id || 'Unknown'}</span
					>
					<p class="text-xs text-surface-500 font-mono">
						State: {data.state || 'Unknown'} | {data.members?.length || 0} members
					</p>
				</div>
			</div>

			<div class="space-y-2 mb-4">
				<div class="flex items-center justify-between text-xs bg-surface-800/40 rounded px-3 py-2">
					<span class="text-surface-400 font-mono">Protocol</span>
					<span class="text-cyan-400 font-mono">{data.protocol || 'N/A'}</span>
				</div>
				<div class="flex items-center justify-between text-xs bg-surface-800/40 rounded px-3 py-2">
					<span class="text-surface-400 font-mono">Coordinator</span>
					<span class="text-cyan-400 font-mono"
						>{data.coordinator?.host || 'N/A'}:{data.coordinator?.port || ''}</span
					>
				</div>
			</div>

			{#if data.members && data.members.length > 0}
				<h4 class="text-xs font-bold font-mono text-surface-400 uppercase tracking-wider mb-2">
					Members
				</h4>
				<div class="space-y-2">
					{#each data.members as member}
						<div class="bg-surface-800/40 rounded p-2 text-xs font-mono">
							<div class="text-cyan-400">{member.client_id}</div>
							<div class="text-surface-500">{member.host}</div>
						</div>
					{/each}
				</div>
			{/if}
		</div>

		<!-- ================================================================ -->
		<!-- Consumer Offsets Result -->
		<!-- ================================================================ -->
	{:else if displayResult.operation === 'get_consumer_group_offsets' && (displayResult.success || displayResult.executed)}
		<div class="retro-card-glow-green rounded-xl p-5">
			<div class="flex items-center gap-2.5 mb-4">
				<div
					class="w-9 h-9 rounded-lg bg-amber-500/20 flex items-center justify-center retro-border-amber"
				>
					<svg
						class="w-5 h-5 text-amber-400"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
						stroke-width="2"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
						/>
					</svg>
				</div>
				<div>
					<span class="text-sm font-bold font-mono text-amber-400"
						>Offsets: {data.group_id || 'Unknown'}</span
					>
					<p class="text-xs text-surface-500 font-mono">{offsets.length} partitions</p>
				</div>
			</div>

			{#if offsets.length > 0}
				<div class="retro-card rounded-lg overflow-hidden">
					<table class="w-full text-xs font-mono">
						<thead>
							<tr class="border-b retro-border bg-surface-900/50">
								<th class="px-3 py-2 text-left text-surface-500">Topic</th>
								<th class="px-3 py-2 text-right text-surface-500">Partition</th>
								<th class="px-3 py-2 text-right text-surface-500">Offset</th>
							</tr>
						</thead>
						<tbody>
							{#each offsets.slice(0, 20) as offset}
								<tr
									class="border-b retro-border last:border-b-0 hover:bg-surface-800/60 transition-colors"
								>
									<td class="px-3 py-2 text-amber-400">{offset.topic}</td>
									<td class="px-3 py-2 text-right text-surface-300">{offset.partition}</td>
									<td class="px-3 py-2 text-right text-surface-300">{offset.offset}</td>
								</tr>
							{/each}
						</tbody>
					</table>
					{#if offsets.length > 20}
						<div class="px-3 py-2 text-xs text-surface-500 bg-surface-900/30">
							... and {offsets.length - 20} more partitions
						</div>
					{/if}
				</div>
			{/if}
		</div>

		<!-- ================================================================ -->
		<!-- Generic Executed Success -->
		<!-- ================================================================ -->
	{:else if displayResult.executed && displayResult.success}
		<div class="retro-card-glow-green rounded-xl p-5">
			<div class="flex items-center gap-2.5 mb-3">
				<StatusIndicator status="active" size="md" pulse />
				<span class="text-sm font-bold font-mono text-emerald-400"
					>{displayResult.operation_name || displayResult.operation || 'Operation Completed'}</span
				>
			</div>
			{#if displayResult.message}
				<p class="text-sm text-surface-300 font-mono">{displayResult.message}</p>
			{/if}

			<!-- Show data if available -->
			{#if Object.keys(data).length > 0}
				<div class="mt-3 space-y-1.5">
					{#each Object.entries(data).slice(0, 10) as [key, value]}
						<div
							class="flex items-center justify-between text-xs bg-surface-800/40 rounded px-2.5 py-1.5"
						>
							<span class="text-surface-400 font-mono">{key}</span>
							<span class="text-emerald-400 font-mono truncate max-w-[60%]">
								{typeof value === 'object' ? JSON.stringify(value).slice(0, 50) : value}
							</span>
						</div>
					{/each}
				</div>
			{/if}
		</div>

		<!-- ================================================================ -->
		<!-- Legacy Success (non-executed) -->
		<!-- ================================================================ -->
	{:else if displayResult.success && !displayResult.pending && !displayResult.needs_info && !displayResult.unclear}
		<div class="retro-card-glow-green rounded-xl p-5">
			<div class="flex items-center gap-2.5 mb-3">
				<StatusIndicator status="active" size="md" pulse />
				<span class="text-sm font-bold font-mono text-emerald-400"
					>{displayResult.operation_title || 'Operation Successful'}</span
				>
			</div>
			{#if displayResult.message}
				<p class="text-sm text-surface-300 font-mono">{displayResult.message}</p>
			{/if}
			{#if displayResult.topic}
				<p class="text-sm text-surface-400 font-mono mt-2">Topic: {displayResult.topic}</p>
			{/if}
			{#if typeof displayResult.partitions === 'number'}
				<p class="text-sm text-surface-400 font-mono">Partitions: {displayResult.partitions}</p>
			{/if}
			{#if displayResult.replication_factor}
				<p class="text-sm text-surface-400 font-mono">
					Replication Factor: {displayResult.replication_factor}
				</p>
			{/if}
		</div>

		<!-- ================================================================ -->
		<!-- Error Card -->
		<!-- ================================================================ -->
	{:else if displayResult.error}
		<div class="retro-card-glow-amber rounded-xl p-5">
			<div class="flex items-center gap-2.5 mb-3">
				<StatusIndicator status="error" size="md" />
				<span class="text-sm font-bold font-mono text-red-400">Operation Failed</span>
			</div>
			<p class="text-sm text-red-300 font-mono">{displayResult.error}</p>
		</div>
	{/if}

	<!-- ================================================================ -->
	<!-- Code Preview (Educational) -->
	<!-- ================================================================ -->
	{#if !isPending && (displayResult.code_executed || displayResult.code_preview)}
		<div class="mt-3">
			<button
				type="button"
				onclick={() => (showCode = !showCode)}
				class="text-xs text-surface-500 hover:text-surface-300 transition-colors flex items-center gap-1"
			>
				<svg
					class="w-3 h-3"
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
					stroke-width="2"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"
					/>
				</svg>
				{showCode ? 'Hide code' : 'View executed code'}
			</button>
			{#if showCode}
				<pre
					class="mt-2 text-xs font-mono bg-surface-900/80 rounded-lg p-3 overflow-x-auto text-surface-300 border border-surface-800">{displayResult.code_executed ||
						displayResult.code_preview}</pre>
			{/if}
		</div>
	{/if}
</div>
