<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { getClusterInfo, type ClusterInfo } from '$lib/api';
	import { Header, Card, Button, Badge, StatusDot } from '$lib/components';
	import { ClusterTopology, MetricsGrid, QuickActions, TopicsList, ConsumerGroupsList } from '$lib/components/cluster';

	let clusterInfo = $state<Partial<ClusterInfo> & { connected: boolean }>({ connected: false });
	let loading = $state(true);
	let error = $state<string | null>(null);
	let showChat = $state(false);

	async function loadClusterData() {
		loading = true;
		error = null;
		try {
			const info = await getClusterInfo().catch(() => ({ connected: false }));
			clusterInfo = info;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load cluster data';
		} finally {
			loading = false;
		}
	}

	function handleQuickAction(action: string) {
		// Open chat drawer with the action pre-filled
		showChat = true;
		// The chat drawer will handle the action
		const actionMessages: Record<string, string> = {
			'list_topics': 'List all topics in the cluster',
			'describe_topic': 'Describe a topic',
			'create_topic': 'Create a new topic',
			'list_consumer_groups': 'List all consumer groups'
		};

		// Dispatch event for chat drawer
		window.dispatchEvent(new CustomEvent('chat-action', {
			detail: { message: actionMessages[action] || action }
		}));
	}

	function handleTopicClick(topic: string) {
		showChat = true;
		window.dispatchEvent(new CustomEvent('chat-action', {
			detail: { message: `Describe topic ${topic}` }
		}));
	}

	function handleGroupClick(group: string) {
		showChat = true;
		window.dispatchEvent(new CustomEvent('chat-action', {
			detail: { message: `Describe consumer group ${group}` }
		}));
	}

	onMount(() => {
		loadClusterData();
		// Refresh every 30 seconds
		const interval = setInterval(loadClusterData, 30000);
		return () => clearInterval(interval);
	});
</script>

<svelte:head>
	<title>Dashboard - kGPT</title>
</svelte:head>

<div class="flex flex-col h-full bg-surface-900">
	<Header title="Cluster Dashboard" subtitle={clusterInfo.connected ? clusterInfo.cluster_id : 'Not connected'}>
		{#snippet actions()}
			<Button variant="ghost" size="sm" onclick={loadClusterData} disabled={loading}>
				{#if loading}
					<svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
						<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
						<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
					</svg>
				{:else}
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
						<path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
					</svg>
				{/if}
				Refresh
			</Button>
			{#if !clusterInfo.connected}
				<Button variant="primary" onclick={() => goto('/connect')}>
					Connect Cluster
				</Button>
			{/if}
			<Button
				variant={showChat ? 'primary' : 'default'}
				onclick={() => showChat = !showChat}
			>
				<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
					<path stroke-linecap="round" stroke-linejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
				</svg>
				AI Assistant
			</Button>
		{/snippet}
	</Header>

	<div class="flex-1 overflow-y-auto">
		<div class="p-6 space-y-6 max-w-7xl mx-auto">
			<!-- Error display -->
			{#if error}
				<Card variant="error" padding="sm">
					<div class="flex items-center gap-2 text-sm">
						<StatusDot status="error" />
						<span class="text-error">{error}</span>
					</div>
				</Card>
			{/if}

			<!-- Loading state -->
			{#if loading && !clusterInfo.connected}
				<div class="flex items-center justify-center py-16">
					<div class="text-center">
						<svg class="w-8 h-8 mx-auto text-primary animate-spin mb-4" fill="none" viewBox="0 0 24 24">
							<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
							<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
						</svg>
						<p class="text-surface-400">Loading cluster information...</p>
					</div>
				</div>
			{:else}
				<!-- Metrics Grid -->
				<MetricsGrid
					brokers={clusterInfo.brokers || 0}
					topics={clusterInfo.topics?.length || 0}
					consumerGroups={clusterInfo.consumer_groups?.length || 0}
					connected={clusterInfo.connected}
					clusterId={clusterInfo.cluster_id}
				/>

				<!-- Quick Actions -->
				{#if clusterInfo.connected}
					<QuickActions onAction={handleQuickAction} disabled={!clusterInfo.connected} />
				{/if}

				<!-- Cluster Topology Visualization -->
				<div>
					<h2 class="text-sm font-semibold text-surface-300 mb-3">Cluster Topology</h2>
					<ClusterTopology
						brokers={clusterInfo.brokers || 0}
						topics={clusterInfo.topics || []}
						consumerGroups={clusterInfo.consumer_groups || []}
						connected={clusterInfo.connected}
					/>
				</div>

				<!-- Topics and Consumer Groups -->
				{#if clusterInfo.connected && (clusterInfo.topics?.length || clusterInfo.consumer_groups?.length)}
					<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
						<TopicsList
							topics={clusterInfo.topics || []}
							onTopicClick={handleTopicClick}
						/>
						<ConsumerGroupsList
							groups={clusterInfo.consumer_groups || []}
							onGroupClick={handleGroupClick}
						/>
					</div>
				{/if}

				<!-- Empty state when not connected -->
				{#if !clusterInfo.connected && !loading}
					<Card class="text-center py-12">
						<svg class="w-16 h-16 mx-auto text-surface-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1">
							<path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
							<path stroke-linecap="round" stroke-linejoin="round" d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
						</svg>
						<h3 class="text-lg font-semibold text-surface-200 mb-2">No Cluster Connected</h3>
						<p class="text-surface-500 mb-6 max-w-md mx-auto">
							Connect to a Kafka cluster to view topology, metrics, and manage your streaming infrastructure.
						</p>
						<Button variant="primary" onclick={() => goto('/connect')}>
							Connect to Cluster
						</Button>
					</Card>
				{/if}
			{/if}
		</div>
	</div>
</div>

<!-- Chat Drawer will be rendered here -->
{#if showChat}
	{#await import('$lib/components/chat/ChatDrawer.svelte') then { default: ChatDrawer }}
		<ChatDrawer onClose={() => showChat = false} />
	{/await}
{/if}
