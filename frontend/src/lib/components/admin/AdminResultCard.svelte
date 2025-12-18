<script lang="ts">
	import type { AdminOperationResult } from '$lib/stores/chat';
	import { executeAdminOperation } from '$lib/api';
	import { isPartitionDetailList } from './types';

	import PendingConfirmation from './PendingConfirmation.svelte';
	import TopicsTable from './TopicsTable.svelte';
	import TopicDetails from './TopicDetails.svelte';
	import ConsumerGroupsTable from './ConsumerGroupsTable.svelte';
	import ConsumerGroupDetails from './ConsumerGroupDetails.svelte';
	import ClusterOverview from './ClusterOverview.svelte';
	import OffsetsTable from './OffsetsTable.svelte';
	import OperationSuccess from './OperationSuccess.svelte';
	import OperationError from './OperationError.svelte';
	import CodePreview from './CodePreview.svelte';

	interface Props {
		result: AdminOperationResult;
		onOperationComplete?: (result: AdminOperationResult) => void;
	}

	let { result, onOperationComplete }: Props = $props();

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

			executionResult = { ...response, executed: true, pending: false };
			onOperationComplete?.(executionResult);
		} catch (error) {
			executionError = error instanceof Error ? error.message : 'Operation failed';
		} finally {
			isExecuting = false;
		}
	}

	function handleCancel() {
		onOperationComplete?.({ success: false, error: 'Operation cancelled by user' });
	}

	const displayResult = $derived(executionResult || result);
	const isPending = $derived(result.pending && !executionResult);

	// Data extraction
	const data = $derived(displayResult.data || {});
	const topics = $derived(data.topics || []);
	const groups = $derived(data.groups || []);
	const brokers = $derived(data.brokers || []);
	const offsets = $derived(data.offsets || []);
	const partitions = $derived(data.partitions || displayResult.partitions);
	const config = $derived(data.configuration || displayResult.configuration || {});

	const codeToShow = $derived(displayResult.code_executed || displayResult.code_preview);
</script>

<div class="admin-result-card">
	{#if isPending}
		<PendingConfirmation
			{result}
			{isExecuting}
			{executionError}
			onConfirm={handleConfirm}
			onCancel={handleCancel}
		/>

	{:else if displayResult.operation === 'list_topics' && (displayResult.success || displayResult.executed)}
		<TopicsTable {topics} totalCount={data.total_count} />

	{:else if displayResult.operation === 'describe_topic' && (displayResult.success || displayResult.executed)}
		<TopicDetails
			topic={data.topic || displayResult.topic || ''}
			partitionCount={data.partition_count || displayResult.partition_count}
			replicationFactor={data.replication_factor || displayResult.replication_factor}
			{partitions}
			{config}
		/>

	{:else if displayResult.operation === 'list_consumer_groups' && (displayResult.success || displayResult.executed)}
		<ConsumerGroupsTable {groups} totalCount={data.total_count} />

	{:else if displayResult.operation === 'describe_cluster' && (displayResult.success || displayResult.executed)}
		<ClusterOverview
			clusterId={data.cluster_id}
			controllerId={data.controller_id}
			brokerCount={data.broker_count}
			topicCount={data.topic_count}
			{brokers}
		/>

	{:else if displayResult.operation === 'describe_consumer_group' && (displayResult.success || displayResult.executed)}
		<ConsumerGroupDetails
			groupId={data.group_id || ''}
			state={data.state}
			protocol={data.protocol}
			coordinator={data.coordinator}
			members={data.members}
		/>

	{:else if displayResult.operation === 'get_consumer_group_offsets' && (displayResult.success || displayResult.executed)}
		<OffsetsTable groupId={data.group_id || ''} {offsets} />

	{:else if displayResult.executed && displayResult.success}
		<OperationSuccess result={displayResult} />

	{:else if displayResult.success && !displayResult.pending && !displayResult.needs_info && !displayResult.unclear}
		<OperationSuccess result={displayResult} />

	{:else if displayResult.error}
		<OperationError error={displayResult.error} />
	{/if}

	{#if !isPending && codeToShow}
		<CodePreview code={codeToShow} />
	{/if}
</div>
