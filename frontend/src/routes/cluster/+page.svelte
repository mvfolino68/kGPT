<script lang="ts">
	import { onMount } from 'svelte';
	import { getClusters, getClusterInfo, connectCluster, disconnectCluster, type KafkaCluster, type ClusterInfo } from '$lib/api';
	import { Header, StatusIndicator } from '$lib/components';
	import { ConnectionStatus, QuickConnect, ConnectForm } from '$lib/components/cluster-page';

	let clusters = $state<KafkaCluster[]>([]);
	let clusterInfo = $state<Partial<ClusterInfo> & { connected: boolean }>({ connected: false });
	let loading = $state(true);
	let connecting = $state(false);
	let error = $state<string | null>(null);

	// Form state
	let showForm = $state(false);
	let formName = $state('');
	let formBootstrap = $state('');
	let formProtocol = $state('PLAINTEXT');

	async function loadData() {
		loading = true;
		error = null;
		try {
			const timeout = new Promise<never>((_, reject) =>
				setTimeout(() => reject(new Error('Request timeout')), 15000)
			);

			const [clustersResult, infoResult] = await Promise.race([
				Promise.all([
					getClusters().catch(() => []),
					getClusterInfo().catch(() => ({ connected: false }))
				]),
				timeout
			]) as [KafkaCluster[], Partial<ClusterInfo> & { connected: boolean }];

			clusters = clustersResult;
			clusterInfo = infoResult;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load cluster data';
			clusters = [];
			clusterInfo = { connected: false };
		} finally {
			loading = false;
		}
	}

	async function handleConnect(cluster?: KafkaCluster) {
		connecting = true;
		error = null;
		try {
			if (cluster) {
				await connectCluster({
					name: cluster.name,
					bootstrap_servers: cluster.bootstrap_servers,
					security_protocol: cluster.security_protocol
				});
			} else {
				await connectCluster({
					name: formName,
					bootstrap_servers: formBootstrap,
					security_protocol: formProtocol
				});
				showForm = false;
				formName = '';
				formBootstrap = '';
				formProtocol = 'PLAINTEXT';
			}
			await loadData();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to connect';
		} finally {
			connecting = false;
		}
	}

	async function handleDisconnect() {
		try {
			await disconnectCluster();
			await loadData();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to disconnect';
		}
	}

	function connectDemo() {
		formName = 'Demo Cluster';
		formBootstrap = 'localhost:9094';
		formProtocol = 'PLAINTEXT';
		showForm = true;
	}

	onMount(() => {
		loadData();
	});
</script>

<svelte:head>
	<title>Cluster - kGPT</title>
</svelte:head>

<div class="flex flex-col h-full bg-surface-900">
	<Header title="Cluster" subtitle="Kafka cluster management">
		{#snippet actions()}
			<button type="button" class="btn btn-ghost btn-sm" onclick={loadData}>
				<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
					<path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
				</svg>
				Refresh
			</button>
		{/snippet}
	</Header>

	<div class="flex-1 overflow-y-auto p-6">
		<div class="max-w-5xl mx-auto space-y-4">
			<!-- Error display -->
			{#if error}
				<div class="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-sm text-red-400 flex items-center gap-2">
					<StatusIndicator status="error" size="sm" />
					<span>{error}</span>
				</div>
			{/if}

			<!-- Connection status -->
			<ConnectionStatus
				{clusterInfo}
				{loading}
				onDisconnect={handleDisconnect}
			/>

			<!-- Quick connect (only when disconnected) -->
			{#if !clusterInfo.connected && !loading}
				<QuickConnect onConnectDemo={connectDemo} />
			{/if}

			<!-- Connect form -->
			<ConnectForm
				{showForm}
				{formName}
				{formBootstrap}
				{formProtocol}
				{connecting}
				{clusters}
				onShowForm={() => showForm = true}
				onHideForm={() => showForm = false}
				onSubmit={() => handleConnect()}
				onConnect={(cluster) => handleConnect(cluster)}
				onNameChange={(v) => formName = v}
				onBootstrapChange={(v) => formBootstrap = v}
				onProtocolChange={(v) => formProtocol = v}
			/>
		</div>
	</div>
</div>
