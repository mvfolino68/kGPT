<script lang="ts">
	import { Card } from '$lib/components/ui';
	import type { TopicInfo, GroupInfo, BrokerInfo, OffsetInfo, MemberInfo, CoordinatorInfo, ConfigEntry, PartitionDetail } from './types';

	import TopicsTable from './TopicsTable.svelte';
	import TopicDetails from './TopicDetails.svelte';
	import ConsumerGroupsTable from './ConsumerGroupsTable.svelte';
	import ConsumerGroupDetails from './ConsumerGroupDetails.svelte';
	import ClusterOverview from './ClusterOverview.svelte';
	import OffsetsTable from './OffsetsTable.svelte';
	import OperationSuccess from './OperationSuccess.svelte';
	import OperationError from './OperationError.svelte';

	interface ToolResult {
		tool_name?: string;
		data?: any;
		// Legacy support
		operation?: string;
		success?: boolean;
		error?: string;
		[key: string]: any;
	}

	interface Props {
		result: ToolResult;
		onOperationComplete?: (result: any) => void;
	}

	let { result, onOperationComplete }: Props = $props();

	// Normalize input: try to get tool_name and data
	// If it's legacy format, map operation to tool_name
	const toolName = $derived(result.tool_name || result.operation);
	const data = $derived(result.data !== undefined ? result.data : result);

	// Helpers to safely cast data
	function asArray<T>(val: any): T[] {
		return Array.isArray(val) ? val : (val?.topics || val?.groups || []);
	}

	function asRecord(val: any): Record<string, any> {
		return (typeof val === 'object' && val !== null) ? val : {};
	}

	// Derived data for components
	const topicData = $derived(asRecord(data));
</script>

<Card padding="none">
	{#snippet children()}
		{#if result.error}
			<OperationError error={result.error} />

		{:else if toolName === 'list_topics'}
			<TopicsTable topics={asArray(data)} totalCount={asArray(data).length} />

		{:else if toolName === 'describe_topic'}
			<TopicDetails
				topic={topicData.name}
				partitionCount={topicData.partition_count}
				replicationFactor={topicData.replication_factor}
				partitions={topicData.partitions}
				config={topicData.config}
			/>

		{:else if toolName === 'list_consumer_groups'}
			<ConsumerGroupsTable groups={asArray(data)} totalCount={asArray(data).length} />

		{:else if toolName === 'describe_consumer_group'}
			<ConsumerGroupDetails
				groupId={topicData.group_id}
				state={topicData.state}
				protocol={topicData.protocol}
				coordinator={topicData.coordinator}
				members={topicData.members}
			/>

		{:else if toolName === 'describe_cluster'}
			<ClusterOverview
				clusterId={topicData.cluster_id}
				controllerId={topicData.controller_id}
				brokerCount={topicData.broker_count}
				topicCount={topicData.topic_count}
				brokers={topicData.brokers}
			/>

		{:else if toolName === 'create_topic' || toolName === 'delete_topic' || toolName === 'delete_consumer_group'}
			{#if topicData.success === false}
				<OperationError error={topicData.message || 'Operation failed'} />
			{:else}
				<OperationSuccess result={{ ...topicData, operation_name: toolName }} />
			{/if}

		{:else}
			<!-- Default Fallback: JSON dump or Success -->
			<div class="p-4 overflow-auto max-h-96">
				{#if topicData.success}
					<OperationSuccess result={{ ...topicData, operation_name: toolName }} />
				{:else}
					<pre class="text-xs text-text-secondary bg-surface-hover p-2 rounded">{JSON.stringify(data, null, 2)}</pre>
				{/if}
			</div>
		{/if}
	{/snippet}
</Card>
