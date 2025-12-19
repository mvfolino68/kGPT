<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { getClusterInfo, connectCluster, type ClusterInfo } from '$lib/api';
	import { Header, Card, Button, Badge, StatusDot } from '$lib/components';
	import { ClusterTopology, MetricsGrid, QuickActions, TopicsList, ConsumerGroupsList } from '$lib/components/cluster';
	import { Hint } from '$lib/components/hints';

	let clusterInfo = $state<Partial<ClusterInfo> & { connected: boolean }>({ connected: false });
	let loading = $state(true);
	let error = $state<string | null>(null);
	let showChat = $state(false);
	let connecting = $state(false);
	let showConnectForm = $state(false);
	let formName = $state('');
	let formBootstrap = $state('');
	let formProtocol = $state('PLAINTEXT');

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
	<Header title="Dashboard" subtitle={clusterInfo.connected ? clusterInfo.cluster_id : 'Connect a Kafka cluster to get started'}>
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
			{#if !clusterInfo.connected && !loading}
				<Button variant="primary" onclick={connectDemo} disabled={connecting}>
					{connecting ? 'Connecting...' : 'Quick Connect'}
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
					<Card class="py-8">
						<div class="text-center mb-8">
							<svg class="w-16 h-16 mx-auto text-surface-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1">
								<path stroke-linecap="round" stroke-linejoin="round" d="M5.25 14.25h13.5m-13.5 0a3 3 0 01-3-3m3 3a3 3 0 100 6h13.5a3 3 0 100-6m-16.5-3a3 3 0 013-3h13.5a3 3 0 013 3m-19.5 0a4.5 4.5 0 01.9-2.7L5.737 5.1a3.375 3.375 0 012.7-1.35h7.126c1.062 0 2.062.5 2.7 1.35l2.587 3.45a4.5 4.5 0 01.9 2.7" />
							</svg>
							<h3 class="text-lg font-semibold text-surface-200 mb-2">Connect to Kafka</h3>
							<p class="text-surface-500 max-w-md mx-auto text-sm">
								Connect to a cluster to view topology, metrics, and manage your streaming infrastructure with AI.
							</p>
						</div>

						{#if !showConnectForm}
							<div class="max-w-md mx-auto space-y-3">
								<button
									type="button"
									class="w-full p-4 rounded-xl bg-surface-800/50 border border-surface-700/50 hover:border-emerald-500/30 hover:bg-surface-800 transition-all text-left group"
									onclick={connectDemo}
									disabled={connecting}
								>
									<div class="flex items-center gap-4">
										<div class="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center">
											<svg class="w-6 h-6 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
												<path stroke-linecap="round" stroke-linejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347a1.125 1.125 0 01-1.667-.985V5.653z" />
											</svg>
										</div>
										<div class="flex-1">
											<h4 class="text-sm font-medium text-surface-100 group-hover:text-emerald-400">Use Demo Cluster</h4>
											<p class="text-xs text-surface-500 mt-0.5">Connect to the local development cluster at localhost:9094</p>
										</div>
										{#if connecting}
											<svg class="w-5 h-5 text-primary animate-spin" fill="none" viewBox="0 0 24 24">
												<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
												<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
											</svg>
										{:else}
											<svg class="w-5 h-5 text-surface-600 group-hover:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
												<path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
											</svg>
										{/if}
									</div>
								</button>

								<button
									type="button"
									class="w-full p-4 rounded-xl bg-surface-800/50 border border-surface-700/50 hover:border-primary/30 hover:bg-surface-800 transition-all text-left group"
									onclick={() => showConnectForm = true}
								>
									<div class="flex items-center gap-4">
										<div class="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
											<svg class="w-6 h-6 text-primary-light" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
												<path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
											</svg>
										</div>
										<div class="flex-1">
											<h4 class="text-sm font-medium text-surface-100 group-hover:text-primary-light">Connect Custom Cluster</h4>
											<p class="text-xs text-surface-500 mt-0.5">Enter your own cluster connection details</p>
										</div>
										<svg class="w-5 h-5 text-surface-600 group-hover:text-primary-light" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
											<path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
										</svg>
									</div>
								</button>

								<p class="text-xs text-surface-500 text-center pt-2">
									Manage saved clusters in <a href="/settings" class="text-primary-light hover:underline">Settings</a>
								</p>
							</div>
						{:else}
							<!-- Inline connect form -->
							<form onsubmit={(e) => { e.preventDefault(); handleConnect(); }} class="max-w-md mx-auto space-y-4">
								<div class="grid grid-cols-2 gap-3">
									<div>
										<label for="dash-cluster-name" class="block text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-1.5">Name</label>
										<input
											id="dash-cluster-name"
											type="text"
											bind:value={formName}
											placeholder="my-cluster"
											class="w-full input"
										/>
									</div>
									<div>
										<label for="dash-protocol" class="block text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-1.5">Protocol</label>
										<select id="dash-protocol" bind:value={formProtocol} class="w-full input">
											<option value="PLAINTEXT">PLAINTEXT</option>
											<option value="SSL">SSL</option>
											<option value="SASL_PLAINTEXT">SASL_PLAINTEXT</option>
											<option value="SASL_SSL">SASL_SSL</option>
										</select>
									</div>
								</div>
								<div>
									<label for="dash-bootstrap" class="block text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-1.5">Bootstrap Servers</label>
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
									<Button type="button" variant="ghost" onclick={() => showConnectForm = false}>
										Cancel
									</Button>
								</div>
							</form>
						{/if}
					</Card>
				{/if}
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
		<ChatDrawer onClose={() => showChat = false} />
	{/await}
{/if}
