<script lang="ts">
	import { onMount } from 'svelte';
	import { getClusters, getClusterInfo, connectCluster, disconnectCluster, type KafkaCluster, type ClusterInfo } from '$lib/api';
	import { RetroHeader, RetroButton, StatusIndicator, RetroCard } from '$lib/components';
	import kafkaLogo from '$lib/assets/kafka-logo.svg';

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

<div class="flex flex-col h-full bg-surface-950">
	<!-- Retro Header -->
	<RetroHeader path="kgpt/cluster" flag="--kafka">
		{#snippet rightContent()}
			<RetroButton size="sm" onclick={loadData}>
				↻ refresh
			</RetroButton>
		{/snippet}
	</RetroHeader>

	<div class="flex-1 overflow-y-auto p-6">
		<div class="max-w-5xl mx-auto space-y-6">

			<!-- Error display -->
			{#if error}
				<div class="retro-card-glow-amber rounded p-3 font-mono text-sm text-red-400 flex items-center gap-2">
					<StatusIndicator status="error" size="sm" />
					<span class="text-red-500">error:</span> {error}
				</div>
			{/if}

			<!-- Connection status - Digital panel style -->
			<RetroCard variant={clusterInfo.connected ? 'glow-green' : 'default'} class="overflow-hidden">
				<div class="flex items-center justify-between border-b retro-border pb-3 mb-4">
					<div class="flex items-center gap-3">
						<StatusIndicator
							status={clusterInfo.connected ? 'active' : 'inactive'}
							size="lg"
							pulse={clusterInfo.connected}
						/>
						<span class="font-mono text-sm text-surface-300 uppercase tracking-wider">Connection Status</span>
					</div>
					{#if loading}
						<span class="font-mono text-xs text-surface-500 animate-pulse-slow">CHECKING...</span>
					{/if}
				</div>

				{#if loading}
					<div class="p-8 text-center font-mono text-surface-500 animate-pulse-slow">
						<StatusIndicator status="warning" pulse />
						<span class="ml-2">scanning for clusters...</span>
					</div>
				{:else if clusterInfo.connected}
					<div class="space-y-4">
						<div class="flex items-center gap-3 mb-4">
							<span class="text-2xl font-bold font-mono text-emerald-400 text-glow-green">CONNECTED</span>
						</div>

						<!-- Digital display stats grid -->
						<div class="grid grid-cols-4 gap-3">
							<div class="retro-card-elevated rounded-lg p-4 text-center">
								<div class="text-xs font-mono text-surface-500 uppercase mb-2 tracking-wider">Cluster ID</div>
								<div class="text-sm font-mono text-emerald-400 truncate" title={clusterInfo.cluster_id}>
									{clusterInfo.cluster_id || '—'}
								</div>
							</div>
							<div class="retro-card-elevated rounded-lg p-4 text-center">
								<div class="text-xs font-mono text-surface-500 uppercase mb-2 tracking-wider">Brokers</div>
								<div class="text-2xl font-bold font-mono text-cyan-400 tabular-nums">
									{clusterInfo.brokers || 0}
								</div>
							</div>
							<div class="retro-card-elevated rounded-lg p-4 text-center">
								<div class="text-xs font-mono text-surface-500 uppercase mb-2 tracking-wider">Topics</div>
								<div class="text-2xl font-bold font-mono text-purple-400 tabular-nums">
									{clusterInfo.topics?.length || 0}
								</div>
							</div>
							<div class="retro-card-elevated rounded-lg p-4 text-center">
								<div class="text-xs font-mono text-surface-500 uppercase mb-2 tracking-wider">Groups</div>
								<div class="text-2xl font-bold font-mono text-amber-400 tabular-nums">
									{clusterInfo.consumer_groups?.length || 0}
								</div>
							</div>
						</div>

						{#if clusterInfo.topics && clusterInfo.topics.length > 0}
							<div class="pt-4 border-t retro-border">
								<div class="flex items-center gap-2 mb-3">
									<span class="text-xs font-mono text-surface-500 uppercase tracking-wider">Topics:</span>
									<span class="text-xs font-mono text-surface-600">[{clusterInfo.topics.length}]</span>
								</div>
								<div class="flex flex-wrap gap-1.5">
									{#each clusterInfo.topics.slice(0, 24) as topic}
										<span class="px-2.5 py-1 text-xs font-mono retro-card rounded">
											{topic}
										</span>
									{/each}
									{#if clusterInfo.topics.length > 24}
										<span class="px-2.5 py-1 text-xs font-mono bg-surface-800/60 text-surface-500 rounded border border-surface-700">
											+{clusterInfo.topics.length - 24} more
										</span>
									{/if}
								</div>
							</div>
						{/if}

						<!-- Operations -->
						<div class="pt-4 border-t retro-border">
							<div class="flex items-center gap-2 mb-3">
								<svg class="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
									<path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
								</svg>
								<span class="text-xs font-mono text-surface-500 uppercase tracking-wider">Available Operations</span>
							</div>
							<div class="grid grid-cols-2 gap-2">
								<a href="/" class="retro-button hover-glow-green flex items-center gap-2 px-3 py-2 text-xs rounded">
									<svg class="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
										<path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
									</svg>
									<span>create topic</span>
								</a>
								<a href="/" class="retro-button hover-glow-cyan flex items-center gap-2 px-3 py-2 text-xs rounded">
									<svg class="w-4 h-4 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
										<path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
									</svg>
									<span>delete topic</span>
								</a>
								<a href="/" class="retro-button hover-glow-cyan flex items-center gap-2 px-3 py-2 text-xs rounded">
									<svg class="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
										<path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
										<path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
									</svg>
									<span>alter config</span>
								</a>
								<a href="/" class="retro-button hover-glow-cyan flex items-center gap-2 px-3 py-2 text-xs rounded">
									<svg class="w-4 h-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
										<path stroke-linecap="round" stroke-linejoin="round" d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
									</svg>
									<span>add partitions</span>
								</a>
							</div>
							<div class="mt-3 px-2 py-1.5 retro-card rounded-lg">
								<p class="text-xs font-mono text-surface-600">
									→ go to <a href="/" class="text-emerald-400 hover:text-emerald-300 hover:underline">chat</a> to perform operations
								</p>
							</div>
						</div>

						<div class="pt-4 border-t retro-border">
							<RetroButton variant="danger" size="sm" onclick={handleDisconnect}>
								disconnect
							</RetroButton>
						</div>
					</div>
				{:else}
					<div class="p-8 text-center">
						<img src={kafkaLogo} alt="Kafka" class="w-16 h-16 mx-auto mb-4 opacity-40" />
						<div class="flex items-center justify-center gap-2 mb-2">
							<StatusIndicator status="inactive" />
							<span class="text-surface-400 font-mono text-sm uppercase tracking-wider">Disconnected</span>
						</div>
						<p class="text-xs text-surface-600 font-mono mt-1">connect to a Kafka cluster below</p>
					</div>
				{/if}
			</RetroCard>

			<!-- Quick connect -->
			{#if !clusterInfo.connected}
				<RetroCard>
					<div class="flex items-center justify-between border-b retro-border pb-3 mb-4">
						<div class="flex items-center gap-2">
							<svg class="w-4 h-4 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
								<path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
							</svg>
							<span class="font-mono text-sm text-surface-300 uppercase tracking-wider">Quick Connect</span>
						</div>
					</div>

					<div class="space-y-3">
						<RetroButton size="sm" onclick={connectDemo} class="w-full">
							Demo Cluster <span class="text-surface-500 ml-1">(docker)</span>
						</RetroButton>
						<p class="text-xs font-mono text-surface-600">
							# running: docker compose --profile demo up?
						</p>
					</div>
				</RetroCard>
			{/if}

			<!-- Connect form -->
			<RetroCard>
				<div class="flex items-center justify-between border-b retro-border pb-3 mb-4">
					<div class="flex items-center gap-2">
						<span class="text-confluent-accent font-mono text-xs">+</span>
						<span class="font-mono text-sm text-surface-300 uppercase tracking-wider">Connect Cluster</span>
					</div>
					{#if !showForm}
						<RetroButton size="sm" onclick={() => showForm = true}>
							+ new
						</RetroButton>
					{/if}
				</div>

				{#if showForm}
					<form onsubmit={(e) => { e.preventDefault(); handleConnect(); }} class="space-y-4">
						<div class="grid grid-cols-12 gap-3">
							<div class="col-span-3">
								<label class="block text-xs font-mono text-surface-500 mb-1 uppercase tracking-wider">Name</label>
								<input
									type="text"
									bind:value={formName}
									placeholder="my-cluster"
									class="w-full retro-input rounded"
								/>
							</div>
							<div class="col-span-5">
								<label class="block text-xs font-mono text-surface-500 mb-1 uppercase tracking-wider">Bootstrap</label>
								<input
									type="text"
									bind:value={formBootstrap}
									placeholder="localhost:9092"
									class="w-full retro-input rounded"
								/>
							</div>
							<div class="col-span-4">
								<label class="block text-xs font-mono text-surface-500 mb-1 uppercase tracking-wider">Protocol</label>
								<select
									bind:value={formProtocol}
									class="w-full retro-input rounded"
								>
									<option value="PLAINTEXT">PLAINTEXT</option>
									<option value="SSL">SSL</option>
									<option value="SASL_PLAINTEXT">SASL_PLAINTEXT</option>
									<option value="SASL_SSL">SASL_SSL</option>
								</select>
							</div>
						</div>

						<div class="flex gap-2">
							<RetroButton
								type="submit"
								variant="primary"
								disabled={connecting || !formName.trim() || !formBootstrap.trim()}
							>
								{connecting ? 'connecting...' : 'connect'}
							</RetroButton>
							<RetroButton
								type="button"
								onclick={() => showForm = false}
							>
								cancel
							</RetroButton>
						</div>
					</form>
				{/if}

				<!-- Saved clusters -->
				{#if clusters.length > 0 && !showForm}
					<div class="border-t retro-border pt-4 mt-4">
						<div class="text-xs font-mono text-surface-500 uppercase tracking-wider mb-3">
							Saved <span class="text-surface-600">[{clusters.length}]</span>
						</div>
						<div class="space-y-2">
							{#each clusters as cluster}
								<div class="flex items-center justify-between retro-card rounded-lg px-4 py-3 hover:bg-surface-800/60 transition-colors">
									<div class="font-mono text-sm flex-1">
										<div class="text-surface-200">{cluster.name}</div>
										<div class="text-surface-500 text-xs">{cluster.bootstrap_servers}</div>
									</div>
									<RetroButton
										size="sm"
										variant="primary"
										onclick={() => handleConnect(cluster)}
										disabled={connecting}
									>
										connect
									</RetroButton>
								</div>
							{/each}
						</div>
					</div>
				{/if}
			</RetroCard>

		</div>
	</div>
</div>
