<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { getClusters, getClusterInfo, connectCluster, disconnectCluster, type KafkaCluster, type ClusterInfo } from '$lib/api';
	import { Header, Card, Button, Badge, StatusDot, Input } from '$lib/components';

	let clusters = $state<KafkaCluster[]>([]);
	let clusterInfo = $state<Partial<ClusterInfo> & { connected: boolean }>({ connected: false });
	let loading = $state(true);
	let connecting = $state(false);
	let error = $state<string | null>(null);
	let success = $state<string | null>(null);

	// Form state
	let showForm = $state(false);
	let formName = $state('');
	let formBootstrap = $state('');
	let formProtocol = $state('PLAINTEXT');

	async function loadData() {
		loading = true;
		error = null;
		try {
			const [clustersResult, infoResult] = await Promise.all([
				getClusters().catch(() => []),
				getClusterInfo().catch(() => ({ connected: false }))
			]);
			clusters = clustersResult;
			clusterInfo = infoResult;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load cluster data';
		} finally {
			loading = false;
		}
	}

	async function handleConnect(cluster?: KafkaCluster) {
		connecting = true;
		error = null;
		success = null;
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
			success = 'Successfully connected to cluster';
			await loadData();
			// Redirect to dashboard after successful connection
			setTimeout(() => goto('/dashboard'), 1000);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to connect';
		} finally {
			connecting = false;
		}
	}

	async function handleDisconnect() {
		try {
			await disconnectCluster();
			success = 'Disconnected from cluster';
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
	<title>Connect Cluster - kGPT</title>
</svelte:head>

<div class="flex flex-col h-full bg-surface-900">
	<Header title="Connect Cluster" subtitle="Manage your Kafka cluster connections">
		{#snippet actions()}
			<Button variant="ghost" size="sm" onclick={loadData} disabled={loading}>
				<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
					<path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
				</svg>
				Refresh
			</Button>
		{/snippet}
	</Header>

	<div class="flex-1 overflow-y-auto">
		<div class="p-6 max-w-2xl mx-auto space-y-6">
			<!-- Messages -->
			{#if error}
				<Card variant="error" padding="sm">
					<div class="flex items-center gap-2 text-sm">
						<StatusDot status="error" />
						<span>{error}</span>
					</div>
				</Card>
			{/if}

			{#if success}
				<Card variant="success" padding="sm">
					<div class="flex items-center gap-2 text-sm">
						<StatusDot status="success" />
						<span>{success}</span>
					</div>
				</Card>
			{/if}

			<!-- Current Connection Status -->
			<Card variant={clusterInfo.connected ? 'success' : 'default'}>
				<div class="flex items-center justify-between mb-4">
					<div class="flex items-center gap-3">
						<StatusDot
							status={clusterInfo.connected ? 'success' : 'inactive'}
							size="lg"
							pulse={clusterInfo.connected}
						/>
						<div>
							<h2 class="font-semibold text-surface-100">Connection Status</h2>
							<p class="text-sm text-surface-500">
								{clusterInfo.connected ? 'Connected to cluster' : 'Not connected'}
							</p>
						</div>
					</div>
					{#if loading}
						<Badge variant="warning">Checking...</Badge>
					{/if}
				</div>

				{#if clusterInfo.connected}
					<div class="grid grid-cols-3 gap-4 mb-4 p-4 bg-surface-800/50 rounded-lg">
						<div class="text-center">
							<p class="text-2xl font-bold text-surface-100">{clusterInfo.brokers || 0}</p>
							<p class="text-xs text-surface-500">Brokers</p>
						</div>
						<div class="text-center">
							<p class="text-2xl font-bold text-surface-100">{clusterInfo.topics?.length || 0}</p>
							<p class="text-xs text-surface-500">Topics</p>
						</div>
						<div class="text-center">
							<p class="text-2xl font-bold text-surface-100">{clusterInfo.consumer_groups?.length || 0}</p>
							<p class="text-xs text-surface-500">Consumer Groups</p>
						</div>
					</div>

					<div class="flex gap-2">
						<Button variant="primary" onclick={() => goto('/dashboard')}>
							Go to Dashboard
						</Button>
						<Button variant="danger" onclick={handleDisconnect}>
							Disconnect
						</Button>
					</div>
				{/if}
			</Card>

			<!-- Quick Connect -->
			{#if !clusterInfo.connected}
				<Card>
					<div class="flex items-center gap-2 mb-4">
						<svg class="w-5 h-5 text-primary-light" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
							<path stroke-linecap="round" stroke-linejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
						</svg>
						<h2 class="font-semibold text-surface-100">Quick Connect</h2>
					</div>

					<div class="space-y-3">
						<Button variant="default" class="w-full justify-start" onclick={connectDemo}>
							<svg class="w-4 h-4 text-surface-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
								<path stroke-linecap="round" stroke-linejoin="round" d="M5.25 14.25h13.5m-13.5 0a3 3 0 01-3-3m3 3a3 3 0 100 6h13.5a3 3 0 100-6m-16.5-3a3 3 0 013-3h13.5a3 3 0 013 3m-19.5 0a4.5 4.5 0 01.9-2.7L5.737 5.1a3.375 3.375 0 012.7-1.35h7.126c1.062 0 2.062.5 2.7 1.35l2.587 3.45a4.5 4.5 0 01.9 2.7m0 0a3 3 0 01-3 3m0 3h.008v.008h-.008v-.008zm0-6h.008v.008h-.008v-.008zm-3 6h.008v.008h-.008v-.008zm0-6h.008v.008h-.008v-.008z" />
							</svg>
							Demo Cluster (localhost:9094)
						</Button>
						<p class="text-xs text-surface-500">
							For local development with Docker Compose
						</p>
					</div>
				</Card>
			{/if}

			<!-- New Connection Form -->
			<Card>
				<div class="flex items-center justify-between mb-4">
					<div class="flex items-center gap-2">
						<svg class="w-5 h-5 text-surface-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
							<path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
						</svg>
						<h2 class="font-semibold text-surface-100">New Connection</h2>
					</div>
					{#if !showForm}
						<Button size="sm" onclick={() => showForm = true}>
							Add Cluster
						</Button>
					{/if}
				</div>

				{#if showForm}
					<form onsubmit={(e) => { e.preventDefault(); handleConnect(); }} class="space-y-4">
						<div>
							<label for="cluster-name" class="block text-sm font-medium text-surface-300 mb-1.5">
								Cluster Name
							</label>
							<input
								type="text"
								id="cluster-name"
								bind:value={formName}
								placeholder="my-cluster"
								class="input"
							/>
						</div>

						<div>
							<label for="bootstrap-servers" class="block text-sm font-medium text-surface-300 mb-1.5">
								Bootstrap Servers
							</label>
							<input
								type="text"
								id="bootstrap-servers"
								bind:value={formBootstrap}
								placeholder="localhost:9092"
								class="input"
							/>
						</div>

						<div>
							<label for="security-protocol" class="block text-sm font-medium text-surface-300 mb-1.5">
								Security Protocol
							</label>
							<select
								id="security-protocol"
								bind:value={formProtocol}
								class="input"
							>
								<option value="PLAINTEXT">PLAINTEXT</option>
								<option value="SSL">SSL</option>
								<option value="SASL_PLAINTEXT">SASL_PLAINTEXT</option>
								<option value="SASL_SSL">SASL_SSL</option>
							</select>
						</div>

						<div class="flex gap-2 pt-2">
							<Button
								type="submit"
								variant="primary"
								loading={connecting}
								disabled={!formName.trim() || !formBootstrap.trim()}
							>
								{connecting ? 'Connecting...' : 'Connect'}
							</Button>
							<Button
								type="button"
								variant="ghost"
								onclick={() => { showForm = false; formName = ''; formBootstrap = ''; }}
							>
								Cancel
							</Button>
						</div>
					</form>
				{/if}

				<!-- Saved Clusters -->
				{#if clusters.length > 0 && !showForm}
					<div class="mt-4 pt-4 border-t border-surface-700/50">
						<p class="text-xs text-surface-500 uppercase tracking-wider mb-3">
							Saved Clusters ({clusters.length})
						</p>
						<div class="space-y-2">
							{#each clusters as cluster}
								<div class="flex items-center justify-between p-3 bg-surface-800/50 rounded-lg">
									<div class="min-w-0">
										<p class="font-medium text-surface-200 truncate">{cluster.name}</p>
										<p class="text-xs text-surface-500 font-mono truncate">{cluster.bootstrap_servers}</p>
									</div>
									<Button
										size="sm"
										variant="primary"
										onclick={() => handleConnect(cluster)}
										loading={connecting}
									>
										Connect
									</Button>
								</div>
							{/each}
						</div>
					</div>
				{/if}
			</Card>
		</div>
	</div>
</div>
