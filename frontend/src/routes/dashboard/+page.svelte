<script lang="ts">
	import { onMount } from 'svelte';
	import {
		getClusterDetails,
		connectCluster,
		type ClusterDetailsResponse
	} from '$lib/api';
	import { Header, HeaderStatus, Card, Button, StatusDot, Input, Select, Icon } from '$lib/components';
	import {
		ClusterHealthCard,
		BrokersGrid,
		TopicsPanel,
		ConsumerGroupsPanel,
		QuickActions,
		ClusterSwitcher
	} from '$lib/components/cluster';
	import { Hint } from '$lib/components/hints';

	let clusterDetails = $state<ClusterDetailsResponse>({
		connected: false,
		cluster_id: null,
		controller_id: null,
		brokers: [],
		broker_count: 0,
		topics: [],
		topic_count: 0,
		total_partitions: 0,
		under_replicated_count: 0,
		consumer_groups: [],
		consumer_group_count: 0,
		error: null
	});
	let loading = $state(true);
	let error = $state<string | null>(null);
	let showChat = $state(false);
	let connecting = $state(false);
	let showConnectForm = $state(false);
	let formName = $state('');
	let formBootstrap = $state('');
	let formProtocol = $state('PLAINTEXT');

	// Auto-refresh interval
	let refreshInterval: ReturnType<typeof setInterval> | null = null;

	const protocolOptions = [
		{ value: 'PLAINTEXT', label: 'PLAINTEXT' },
		{ value: 'SSL', label: 'SSL' },
		{ value: 'SASL_PLAINTEXT', label: 'SASL_PLAINTEXT' },
		{ value: 'SASL_SSL', label: 'SASL_SSL' }
	];

	async function loadClusterData() {
		loading = true;
		error = null;
		try {
			const details = await getClusterDetails();
			clusterDetails = details;
			if (details.error) {
				error = details.error;
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load cluster data';
		} finally {
			loading = false;
		}
	}

	async function handleConnect(bootstrap?: string, name?: string) {
		connecting = true;
		error = null;
		try {
			await connectCluster({
				name: name || formName || 'Cluster',
				bootstrap_servers: bootstrap || formBootstrap,
				security_protocol: formProtocol
			});
			await loadClusterData();
			showConnectForm = false;
			formName = '';
			formBootstrap = '';
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to connect';
		} finally {
			connecting = false;
		}
	}

	function connectDemo() {
		handleConnect('localhost:9094', 'Demo Cluster');
	}

	function handleQuickAction(action: string) {
		showChat = true;
		const actionMessages: Record<string, string> = {
			list_topics: 'List all topics in the cluster',
			describe_topic: 'Describe a topic',
			create_topic: 'Create a new topic',
			list_consumer_groups: 'List all consumer groups'
		};
		window.dispatchEvent(
			new CustomEvent('chat-action', {
				detail: { message: actionMessages[action] || action }
			})
		);
	}

	function handleTopicClick(topic: string) {
		showChat = true;
		window.dispatchEvent(
			new CustomEvent('chat-action', {
				detail: { message: `Describe topic ${topic}` }
			})
		);
	}

	function handleGroupClick(group: string) {
		showChat = true;
		window.dispatchEvent(
			new CustomEvent('chat-action', {
				detail: { message: `Describe consumer group ${group}` }
			})
		);
	}

	function handleBrokerClick(brokerId: number) {
		showChat = true;
		window.dispatchEvent(
			new CustomEvent('chat-action', {
				detail: { message: `Describe broker ${brokerId} configuration` }
			})
		);
	}

	onMount(() => {
		loadClusterData();
		refreshInterval = setInterval(loadClusterData, 15000);
		return () => {
			if (refreshInterval) clearInterval(refreshInterval);
		};
	});
</script>

<svelte:head>
	<title>Dashboard - kGPT</title>
</svelte:head>

<div class="flex flex-col h-full bg-bg">
	<Header
		title="Kafka Dashboard"
		subtitle={clusterDetails.connected
			? `Cluster ${clusterDetails.cluster_id || ''}`
			: 'Connect to monitor your Kafka cluster'}
	>
		{#snippet actions()}
			<div class="flex items-center gap-4">
				{#if clusterDetails.connected}
					<HeaderStatus status="active" label="Connected" pulse />
				{:else if loading}
					<HeaderStatus status="warning" label="Loading" pulse />
				{:else}
					<HeaderStatus status="inactive" label="Disconnected" />
				{/if}
				<ClusterSwitcher
					currentClusterId={clusterDetails.cluster_id}
					onSwitch={loadClusterData}
				/>
				<Button variant="ghost" size="sm" onclick={loadClusterData} disabled={loading}>
					{loading ? 'Loading...' : 'Refresh'}
				</Button>
				{#if !clusterDetails.connected && !loading}
					<Button variant="primary" size="sm" onclick={connectDemo} loading={connecting}>
						Quick Connect
					</Button>
				{/if}
				<Button variant={showChat ? 'primary' : 'ghost'} size="sm" onclick={() => (showChat = !showChat)}>
					AI Assistant
				</Button>
			</div>
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
			{#if loading && !clusterDetails.connected}
				<div class="flex items-center justify-center py-16">
					<div class="text-center">
						<Icon name="spinner" size="xl" class="mx-auto text-primary animate-spin mb-4" />
						<p class="text-text-secondary">Loading cluster information...</p>
					</div>
				</div>
			{:else if clusterDetails.connected}
				<!-- Connected: Show full dashboard -->

				<!-- Cluster Health Overview -->
				<ClusterHealthCard
					connected={clusterDetails.connected}
					clusterId={clusterDetails.cluster_id}
					controllerId={clusterDetails.controller_id}
					brokerCount={clusterDetails.broker_count}
					topicCount={clusterDetails.topic_count}
					totalPartitions={clusterDetails.total_partitions}
					underReplicatedCount={clusterDetails.under_replicated_count}
					consumerGroupCount={clusterDetails.consumer_group_count}
				/>

				<!-- Quick Actions -->
				<QuickActions onAction={handleQuickAction} disabled={!clusterDetails.connected} />

				<!-- Brokers Grid -->
				{#if clusterDetails.brokers.length > 0}
					<BrokersGrid brokers={clusterDetails.brokers} onBrokerClick={handleBrokerClick} />
				{/if}

				<!-- Topics and Consumer Groups side by side -->
				<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
					<TopicsPanel topics={clusterDetails.topics} onTopicClick={handleTopicClick} />
					<ConsumerGroupsPanel
						groups={clusterDetails.consumer_groups}
						onGroupClick={handleGroupClick}
					/>
				</div>
			{:else}
				<!-- Not connected: Show connection options -->
				<Card class="py-8">
					<div class="text-center mb-8">
						<Icon name="server" size="xl" class="mx-auto text-text-tertiary mb-4 w-16 h-16" />
						<h3 class="text-lg font-semibold text-text-secondary mb-2">Connect to Kafka</h3>
						<p class="text-text-tertiary max-w-md mx-auto text-sm">
							Connect to a cluster to view brokers, topics, consumer groups, and manage your
							streaming infrastructure.
						</p>
					</div>

					{#if !showConnectForm}
						<div class="max-w-md mx-auto space-y-3">
							<button
								type="button"
								class="w-full p-4 rounded-lg bg-surface-hover hover:bg-surface-active transition-colors text-left group"
								onclick={connectDemo}
								disabled={connecting}
							>
								<div class="flex items-center gap-4">
									<div class="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
										<Icon name="play" size="lg" class="text-primary" />
									</div>
									<div class="flex-1">
										<h4 class="text-sm font-medium text-text group-hover:text-text">
											Use Demo Cluster
										</h4>
										<p class="text-xs text-text-tertiary mt-0.5">
											Connect to the local development cluster at localhost:9094
										</p>
									</div>
									{#if connecting}
										<Icon name="spinner" size="md" class="text-primary animate-spin" />
									{:else}
										<Icon name="chevron-right" size="md" class="text-text-tertiary group-hover:text-text-secondary" />
									{/if}
								</div>
							</button>

							<button
								type="button"
								class="w-full p-4 rounded-lg bg-surface-hover hover:bg-surface-active transition-colors text-left group"
								onclick={() => (showConnectForm = true)}
							>
								<div class="flex items-center gap-4">
									<div class="w-12 h-12 rounded-xl bg-surface-active flex items-center justify-center">
										<Icon name="plus" size="lg" class="text-text-secondary" />
									</div>
									<div class="flex-1">
										<h4 class="text-sm font-medium text-text group-hover:text-text">
											Connect Custom Cluster
										</h4>
										<p class="text-xs text-text-tertiary mt-0.5">
											Enter your own cluster connection details
										</p>
									</div>
									<Icon name="chevron-right" size="md" class="text-text-tertiary group-hover:text-text-secondary" />
								</div>
							</button>

							<p class="text-xs text-text-tertiary text-center pt-2">
								Manage saved clusters in <a href="/settings" class="text-text-secondary hover:underline">Settings</a>
							</p>
						</div>
					{:else}
						<!-- Inline connect form -->
						<form
							onsubmit={(e) => {
								e.preventDefault();
								handleConnect();
							}}
							class="max-w-md mx-auto space-y-4"
						>
							<div class="grid grid-cols-2 gap-3">
								<div>
									<label for="dash-cluster-name" class="label block mb-1.5">Name</label>
									<Input
										id="dash-cluster-name"
										type="text"
										bind:value={formName}
										placeholder="my-cluster"
									/>
								</div>
								<div>
									<label for="dash-protocol" class="label block mb-1.5">Protocol</label>
									<Select
										id="dash-protocol"
										bind:value={formProtocol}
										options={protocolOptions}
									/>
								</div>
							</div>
							<div>
								<label for="dash-bootstrap" class="label block mb-1.5">Bootstrap Servers</label>
								<Input
									id="dash-bootstrap"
									type="text"
									bind:value={formBootstrap}
									placeholder="localhost:9092"
								/>
							</div>
							<div class="flex gap-2">
								<Button
									type="submit"
									variant="primary"
									disabled={connecting || !formName.trim() || !formBootstrap.trim()}
									loading={connecting}
								>
									Connect
								</Button>
								<Button type="button" variant="ghost" onclick={() => (showConnectForm = false)}>
									Cancel
								</Button>
							</div>
						</form>
					{/if}
				</Card>
			{/if}
		</div>
	</div>
</div>

<!-- Contextual Hint -->
<Hint
	id="dashboard"
	title="Chat with Your Cluster"
	description="Use natural language to manage Kafka topics, consumer groups, and configurations. Click 'AI Assistant' to start chatting."
/>

<!-- Chat Drawer will be rendered here -->
{#if showChat}
	{#await import('$lib/components/chat/ChatDrawer.svelte') then { default: ChatDrawer }}
		<ChatDrawer onClose={() => (showChat = false)} />
	{/await}
{/if}
