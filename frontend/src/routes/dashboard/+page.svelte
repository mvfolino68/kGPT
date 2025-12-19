<script lang="ts">
	import { onMount } from 'svelte';
	import {
		getClusterDetails,
		connectCluster,
		type ClusterDetailsResponse
	} from '$lib/api';
	import { Header, HeaderStatus, Card, Button, StatusDot, ClickableCard } from '$lib/components';
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
		// Refresh every 15 seconds for more real-time feel
		refreshInterval = setInterval(loadClusterData, 15000);
		return () => {
			if (refreshInterval) clearInterval(refreshInterval);
		};
	});
</script>

<svelte:head>
	<title>Dashboard - kGPT</title>
</svelte:head>

<div class="flex flex-col h-full bg-surface-900">
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
						<svg
							class="w-8 h-8 mx-auto text-primary animate-spin mb-4"
							fill="none"
							viewBox="0 0 24 24"
						>
							<circle
								class="opacity-25"
								cx="12"
								cy="12"
								r="10"
								stroke="currentColor"
								stroke-width="4"
							></circle>
							<path
								class="opacity-75"
								fill="currentColor"
								d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
							></path>
						</svg>
						<p class="text-surface-400">Loading cluster information...</p>
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
						<svg
							class="w-16 h-16 mx-auto text-surface-600 mb-4"
							fill="none"
							stroke="currentColor"
							viewBox="0 0 24 24"
							stroke-width="1"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								d="M5.25 14.25h13.5m-13.5 0a3 3 0 01-3-3m3 3a3 3 0 100 6h13.5a3 3 0 100-6m-16.5-3a3 3 0 013-3h13.5a3 3 0 013 3m-19.5 0a4.5 4.5 0 01.9-2.7L5.737 5.1a3.375 3.375 0 012.7-1.35h7.126c1.062 0 2.062.5 2.7 1.35l2.587 3.45a4.5 4.5 0 01.9 2.7"
							/>
						</svg>
						<h3 class="text-lg font-semibold text-surface-200 mb-2">Connect to Kafka</h3>
						<p class="text-surface-500 max-w-md mx-auto text-sm">
							Connect to a cluster to view brokers, topics, consumer groups, and manage your
							streaming infrastructure.
						</p>
					</div>

					{#if !showConnectForm}
						<div class="max-w-md mx-auto space-y-3">
							<ClickableCard
								variant="subtle"
								class="group"
								onclick={connectDemo}
								disabled={connecting}
							>
								<div class="flex items-center gap-4">
									<div
										class="w-12 h-12 rounded-xl bg-surface-700/50 flex items-center justify-center"
									>
										<svg
											class="w-6 h-6 text-surface-300"
											fill="none"
											stroke="currentColor"
											viewBox="0 0 24 24"
											stroke-width="1.5"
										>
											<path
												stroke-linecap="round"
												stroke-linejoin="round"
												d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347a1.125 1.125 0 01-1.667-.985V5.653z"
											/>
										</svg>
									</div>
									<div class="flex-1">
										<h4 class="text-sm font-medium text-surface-100 group-hover:text-surface-50">
											Use Demo Cluster
										</h4>
										<p class="text-xs text-surface-500 mt-0.5">
											Connect to the local development cluster at localhost:9094
										</p>
									</div>
									{#if connecting}
										<svg class="w-5 h-5 text-primary animate-spin" fill="none" viewBox="0 0 24 24">
											<circle
												class="opacity-25"
												cx="12"
												cy="12"
												r="10"
												stroke="currentColor"
												stroke-width="4"
											></circle>
											<path
												class="opacity-75"
												fill="currentColor"
												d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
											></path>
										</svg>
									{:else}
										<svg
											class="w-5 h-5 text-surface-600 group-hover:text-surface-400"
											fill="none"
											stroke="currentColor"
											viewBox="0 0 24 24"
											stroke-width="1.5"
										>
											<path
												stroke-linecap="round"
												stroke-linejoin="round"
												d="M8.25 4.5l7.5 7.5-7.5 7.5"
											/>
										</svg>
									{/if}
								</div>
							</ClickableCard>

							<ClickableCard
								variant="subtle"
								class="group"
								onclick={() => (showConnectForm = true)}
							>
								<div class="flex items-center gap-4">
									<div
										class="w-12 h-12 rounded-xl bg-surface-700/50 flex items-center justify-center"
									>
										<svg
											class="w-6 h-6 text-surface-300"
											fill="none"
											stroke="currentColor"
											viewBox="0 0 24 24"
											stroke-width="1.5"
										>
											<path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
										</svg>
									</div>
									<div class="flex-1">
										<h4 class="text-sm font-medium text-surface-100 group-hover:text-surface-50">
											Connect Custom Cluster
										</h4>
										<p class="text-xs text-surface-500 mt-0.5">
											Enter your own cluster connection details
										</p>
									</div>
									<svg
										class="w-5 h-5 text-surface-600 group-hover:text-surface-400"
										fill="none"
										stroke="currentColor"
										viewBox="0 0 24 24"
										stroke-width="1.5"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											d="M8.25 4.5l7.5 7.5-7.5 7.5"
										/>
									</svg>
								</div>
							</ClickableCard>

							<p class="text-xs text-surface-500 text-center pt-2">
								Manage saved clusters in <a href="/settings" class="text-surface-300 hover:underline"
									>Settings</a
								>
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
									<label
										for="dash-cluster-name"
										class="block text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-1.5"
										>Name</label
									>
									<input
										id="dash-cluster-name"
										type="text"
										bind:value={formName}
										placeholder="my-cluster"
										class="w-full input"
									/>
								</div>
								<div>
									<label
										for="dash-protocol"
										class="block text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-1.5"
										>Protocol</label
									>
									<select id="dash-protocol" bind:value={formProtocol} class="w-full input">
										<option value="PLAINTEXT">PLAINTEXT</option>
										<option value="SSL">SSL</option>
										<option value="SASL_PLAINTEXT">SASL_PLAINTEXT</option>
										<option value="SASL_SSL">SASL_SSL</option>
									</select>
								</div>
							</div>
							<div>
								<label
									for="dash-bootstrap"
									class="block text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-1.5"
									>Bootstrap Servers</label
								>
								<input
									id="dash-bootstrap"
									type="text"
									bind:value={formBootstrap}
									placeholder="localhost:9092"
									class="w-full input"
								/>
							</div>
							<div class="flex gap-2">
								<Button
									type="submit"
									variant="primary"
									disabled={connecting || !formName.trim() || !formBootstrap.trim()}
								>
									{connecting ? 'Connecting...' : 'Connect'}
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
