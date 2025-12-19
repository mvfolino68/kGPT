<script lang="ts">
	import type { AdminOperationResult } from '$lib/stores/chat';
	import { executeAdminOperation } from '$lib/api';
	import { Card } from '$lib/components/ui';
	import type { TopicInfo, GroupInfo, BrokerInfo, OffsetInfo, MemberInfo, CoordinatorInfo, ConfigEntry, PartitionDetail } from './types';

	import PendingConfirmation from './PendingConfirmation.svelte';
	import NeedsInfoForm from './NeedsInfoForm.svelte';
	import UnclearOperation from './UnclearOperation.svelte';
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
	let executionError: string | null = $state(null);
	let executionResult: AdminOperationResult | null = $state(null);

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

	const displayResult: AdminOperationResult = $derived(executionResult || result);
	const isPending = $derived(result.pending && !executionResult);
	const needsInfo = $derived(result.needs_info && !executionResult);
	const isUnclear = $derived(result.unclear && !executionResult);

	// Data extraction
	type DataRecord = Record<string, unknown>;

	function isRecord(value: unknown): value is Record<string, unknown> {
		return typeof value === 'object' && value !== null && !Array.isArray(value);
	}

	function asRecord(value: unknown): DataRecord {
		return isRecord(value) ? (value as DataRecord) : {};
	}

	function asString(value: unknown): string | undefined {
		return typeof value === 'string' ? value : undefined;
	}

	function asNumber(value: unknown): number | undefined {
		return typeof value === 'number' && Number.isFinite(value) ? value : undefined;
	}

	function asArray<T>(value: unknown): T[] {
		return Array.isArray(value) ? (value as T[]) : [];
	}

	function asCoordinator(value: unknown): CoordinatorInfo | undefined {
		if (!isRecord(value)) return undefined;
		const host = asString(value.host);
		const port = asNumber(value.port);
		if (!host) return undefined;
		return { host, port: port ?? 0 };
	}

	function asConfigRecord(value: unknown): Record<string, ConfigEntry> | undefined {
		if (!isRecord(value)) return undefined;
		const rec = value as Record<string, ConfigEntry>;
		return Object.keys(rec).length > 0 ? rec : undefined;
	}

	const data: DataRecord = $derived(asRecord(displayResult.data));

	const totalCount: number | undefined = $derived(asNumber(data['total_count']));
	const topics: (string | TopicInfo)[] = $derived(asArray<string | TopicInfo>(data['topics']));
	const groups: (string | GroupInfo)[] = $derived(asArray<string | GroupInfo>(data['groups']));
	const brokers: BrokerInfo[] = $derived(asArray<BrokerInfo>(data['brokers']));
	const offsets: OffsetInfo[] = $derived(asArray<OffsetInfo>(data['offsets']));

	const topic: string = $derived(asString(data['topic']) ?? asString((displayResult as unknown as DataRecord)['topic']) ?? '');
	const partitionCount: number | undefined = $derived(
		asNumber(data['partition_count']) ?? asNumber((displayResult as unknown as DataRecord)['partition_count'])
	);
	const replicationFactor: number | undefined = $derived(
		asNumber(data['replication_factor']) ?? asNumber((displayResult as unknown as DataRecord)['replication_factor'])
	);

	const partitions: number | PartitionDetail[] | undefined = $derived(
		(data['partitions'] ?? (displayResult as unknown as DataRecord)['partitions']) as
			| number
			| PartitionDetail[]
			| undefined
	);
	const config: Record<string, ConfigEntry> | undefined = $derived(
		asConfigRecord(data['configuration']) ?? asConfigRecord((displayResult as unknown as DataRecord)['configuration'])
	);

	const clusterId: string | undefined = $derived(asString(data['cluster_id']));
	const controllerId: number | undefined = $derived(asNumber(data['controller_id']));
	const brokerCount: number | undefined = $derived(asNumber(data['broker_count']));
	const topicCount: number | undefined = $derived(asNumber(data['topic_count']));

	const groupId: string = $derived(asString(data['group_id']) ?? '');
	const groupState: string | undefined = $derived(asString(data['state']));
	const protocol: string | undefined = $derived(asString(data['protocol']));
	const coordinator: CoordinatorInfo | undefined = $derived(asCoordinator(data['coordinator']));
	const members: MemberInfo[] = $derived(asArray<MemberInfo>(data['members']));

	const codeToShow = $derived(displayResult.code_executed || displayResult.code_preview);
</script>

<Card padding="none">
	{#snippet children()}
		{#if isPending}
			<PendingConfirmation
				{result}
				{isExecuting}
				{executionError}
				onConfirm={handleConfirm}
				onCancel={handleCancel}
			/>

		{:else if needsInfo}
			<NeedsInfoForm {result} onComplete={onOperationComplete} />

		{:else if isUnclear}
			<UnclearOperation {result} />

		{:else if displayResult.operation === 'list_topics' && (displayResult.success || displayResult.executed)}
			<TopicsTable {topics} {totalCount} />

		{:else if displayResult.operation === 'describe_topic' && (displayResult.success || displayResult.executed)}
			<TopicDetails
				{topic}
				{partitionCount}
				{replicationFactor}
				{partitions}
				{config}
			/>

		{:else if displayResult.operation === 'list_consumer_groups' && (displayResult.success || displayResult.executed)}
			<ConsumerGroupsTable {groups} {totalCount} />

		{:else if displayResult.operation === 'describe_cluster' && (displayResult.success || displayResult.executed)}
			<ClusterOverview
				{clusterId}
				{controllerId}
				{brokerCount}
				{topicCount}
				{brokers}
			/>

		{:else if displayResult.operation === 'describe_consumer_group' && (displayResult.success || displayResult.executed)}
			<ConsumerGroupDetails
				{groupId}
				state={groupState}
				{protocol}
				{coordinator}
				{members}
			/>

		{:else if displayResult.operation === 'get_consumer_group_offsets' && (displayResult.success || displayResult.executed)}
			<OffsetsTable groupId={groupId} {offsets} />

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
	{/snippet}
</Card>
