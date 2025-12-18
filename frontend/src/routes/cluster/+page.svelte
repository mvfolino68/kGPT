<script lang="ts">
	import { onMount } from 'svelte';
	import { getClusters, getClusterInfo, connectCluster, disconnectCluster, type KafkaCluster, type ClusterInfo } from '$lib/api';
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
			// Add timeout to prevent hanging
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
				// Connect using form values
				await connectCluster({
					name: formName,
					bootstrap_servers: formBootstrap,
					security_protocol: formProtocol
				});
				// Reset form
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

<div class="flex flex-col h-full bg-surface-900">
	<!-- Terminal-style header -->
	<header class="px-6 py-4 border-b border-surface-700 bg-surface-800/50">
		<div class="flex items-center gap-3">
			<span class="text-emerald-400 font-mono text-sm">$</span>
			<h1 class="font-mono text-lg text-surface-100">kgpt/cluster</h1>
			<span class="text-surface-500 font-mono text-sm">--kafka</span>
			<button onclick={loadData} class="ml-auto text-surface-500 hover:text-surface-300 font-mono text-xs">
				↻ refresh
			</button>
		</div>
	</header>

	<div class="flex-1 overflow-y-auto p-6">
		<div class="max-w-4xl mx-auto space-y-6">

			<!-- Error display -->
			{#if error}
				<div class="bg-red-900/20 border border-red-800 rounded p-3 font-mono text-sm text-red-400">
					<span class="text-red-500">error:</span> {error}
				</div>
			{/if}

			<!-- Connection status -->
			<section class="bg-surface-800 border border-surface-700 rounded">
				<div class="px-4 py-2 border-b border-surface-700 flex items-center gap-2">
					<span class="{clusterInfo.connected ? 'text-emerald-400' : 'text-surface-500'} font-mono text-xs">●</span>
					<span class="font-mono text-sm text-surface-300">status</span>
				</div>

				{#if loading}
					<div class="p-8 text-center font-mono text-surface-500">
						<span class="animate-pulse">checking connection...</span>
					</div>
				{:else if clusterInfo.connected}
					<div class="p-4 space-y-4">
						<div class="flex items-center gap-3">
							<span class="text-emerald-400 font-mono text-sm">connected</span>
						</div>

						<!-- Cluster stats grid -->
						<div class="grid grid-cols-12 gap-2 text-xs font-mono">
							<div class="col-span-3 bg-surface-900/50 rounded p-3 border border-surface-700">
								<p class="text-surface-500 mb-1">cluster_id</p>
								<p class="text-surface-200 truncate" title={clusterInfo.cluster_id}>{clusterInfo.cluster_id || '—'}</p>
							</div>
							<div class="col-span-3 bg-surface-900/50 rounded p-3 border border-surface-700">
								<p class="text-surface-500 mb-1">brokers</p>
								<p class="text-surface-200">{clusterInfo.brokers || 0}</p>
							</div>
							<div class="col-span-3 bg-surface-900/50 rounded p-3 border border-surface-700">
								<p class="text-surface-500 mb-1">topics</p>
								<p class="text-surface-200">{clusterInfo.topics?.length || 0}</p>
							</div>
							<div class="col-span-3 bg-surface-900/50 rounded p-3 border border-surface-700">
								<p class="text-surface-500 mb-1">consumer_groups</p>
								<p class="text-surface-200">{clusterInfo.consumer_groups?.length || 0}</p>
							</div>
						</div>

						{#if clusterInfo.topics && clusterInfo.topics.length > 0}
							<div>
								<p class="text-xs font-mono text-surface-500 mb-2"># topics:</p>
								<div class="flex flex-wrap gap-1">
									{#each clusterInfo.topics.slice(0, 20) as topic}
										<span class="px-2 py-0.5 text-xs font-mono bg-surface-900 text-surface-400 rounded border border-surface-700">
											{topic}
										</span>
									{/each}
									{#if clusterInfo.topics.length > 20}
										<span class="px-2 py-0.5 text-xs font-mono bg-surface-900 text-surface-500 rounded border border-surface-700">
											+{clusterInfo.topics.length - 20} more
										</span>
									{/if}
								</div>
							</div>
						{/if}

						<!-- Available Admin Operations -->
						<div class="pt-4 border-t border-surface-700">
							<p class="text-xs font-mono text-surface-500 mb-3"># available operations:</p>
							<div class="grid grid-cols-2 gap-2">
								<a
									href="/"
									class="flex items-center gap-2 px-3 py-2 text-xs font-mono bg-surface-900/50 hover:bg-emerald-600/10 border border-surface-700 hover:border-emerald-600/50 rounded transition-colors group"
								>
									<svg class="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
									</svg>
									<span class="text-surface-400 group-hover:text-surface-200">create topic</span>
								</a>
								<a
									href="/"
									class="flex items-center gap-2 px-3 py-2 text-xs font-mono bg-surface-900/50 hover:bg-red-600/10 border border-surface-700 hover:border-red-600/50 rounded transition-colors group"
								>
									<svg class="w-4 h-4 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
									</svg>
									<span class="text-surface-400 group-hover:text-surface-200">delete topic</span>
								</a>
								<a
									href="/"
									class="flex items-center gap-2 px-3 py-2 text-xs font-mono bg-surface-900/50 hover:bg-blue-600/10 border border-surface-700 hover:border-blue-600/50 rounded transition-colors group"
								>
									<svg class="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
									</svg>
									<span class="text-surface-400 group-hover:text-surface-200">alter config</span>
								</a>
								<a
									href="/"
									class="flex items-center gap-2 px-3 py-2 text-xs font-mono bg-surface-900/50 hover:bg-purple-600/10 border border-surface-700 hover:border-purple-600/50 rounded transition-colors group"
								>
									<svg class="w-4 h-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
									</svg>
									<span class="text-surface-400 group-hover:text-surface-200">add partitions</span>
								</a>
							</div>
							<p class="text-xs font-mono text-surface-600 mt-3">
								→ go to <a href="/" class="text-emerald-400 hover:underline">chat</a> to perform operations
							</p>
						</div>

						<button
							type="button"
							onclick={handleDisconnect}
							class="px-3 py-1.5 text-xs font-mono bg-red-600/20 text-red-400 hover:bg-red-600/30 rounded border border-red-600/50"
						>
							disconnect
						</button>
					</div>
				{:else}
					<div class="p-6 text-center">
						<img src={kafkaLogo} alt="Kafka" class="w-12 h-12 mx-auto mb-3 opacity-50" />
						<span class="text-surface-500 font-mono text-sm">not connected</span>
						<p class="text-xs text-surface-600 font-mono mt-1">connect to a Kafka cluster below</p>
					</div>
				{/if}
			</section>

			<!-- Quick connect -->
			{#if !clusterInfo.connected}
				<section class="bg-surface-800 border border-surface-700 rounded">
					<div class="px-4 py-2 border-b border-surface-700 flex items-center gap-2">
						<span class="text-blue-400 font-mono text-xs">⚡</span>
						<span class="font-mono text-sm text-surface-300">quick-connect</span>
					</div>

					<div class="p-4 space-y-3">
						<div class="flex flex-wrap gap-2">
							<button
								type="button"
								onclick={connectDemo}
								class="px-3 py-1.5 font-mono text-xs bg-surface-700 hover:bg-surface-600 text-surface-300 rounded border border-surface-600 hover:border-surface-500 transition-colors"
							>
								🎮 demo-cluster<span class="text-surface-500 ml-1">(docker)</span>
							</button>
						</div>
						<p class="text-xs font-mono text-surface-600">
							# running docker compose --profile demo up?
						</p>
					</div>
				</section>
			{/if}

			<!-- Connect form -->
			<section class="bg-surface-800 border border-surface-700 rounded">
				<div class="px-4 py-2 border-b border-surface-700 flex items-center justify-between">
					<div class="flex items-center gap-2">
						<span class="text-emerald-400 font-mono text-xs">+</span>
						<span class="font-mono text-sm text-surface-300">connect --cluster</span>
					</div>
					{#if !showForm}
						<button
							type="button"
							onclick={() => showForm = true}
							class="text-surface-500 hover:text-surface-300 font-mono text-xs"
						>
							+ new
						</button>
					{/if}
				</div>

				{#if showForm}
					<div class="p-4">
						<form onsubmit={(e) => { e.preventDefault(); handleConnect(); }} class="space-y-4">
							<div class="grid grid-cols-12 gap-3">
								<div class="col-span-3">
									<label class="block text-xs font-mono text-surface-500 mb-1">--name</label>
									<input
										type="text"
										bind:value={formName}
										placeholder="my-cluster"
										class="w-full px-2 py-1.5 bg-surface-900 border border-surface-600 rounded font-mono text-sm text-surface-100 placeholder-surface-600 focus:outline-none focus:border-emerald-500"
									/>
								</div>
								<div class="col-span-5">
									<label class="block text-xs font-mono text-surface-500 mb-1">--bootstrap</label>
									<input
										type="text"
										bind:value={formBootstrap}
										placeholder="localhost:9092"
										class="w-full px-2 py-1.5 bg-surface-900 border border-surface-600 rounded font-mono text-sm text-surface-100 placeholder-surface-600 focus:outline-none focus:border-emerald-500"
									/>
								</div>
								<div class="col-span-4">
									<label class="block text-xs font-mono text-surface-500 mb-1">--protocol</label>
									<select
										bind:value={formProtocol}
										class="w-full px-2 py-1.5 bg-surface-900 border border-surface-600 rounded font-mono text-sm text-surface-100 focus:outline-none focus:border-emerald-500"
									>
										<option value="PLAINTEXT">PLAINTEXT</option>
										<option value="SSL">SSL</option>
										<option value="SASL_PLAINTEXT">SASL_PLAINTEXT</option>
										<option value="SASL_SSL">SASL_SSL</option>
									</select>
								</div>
							</div>

							<div class="flex gap-2">
								<button
									type="submit"
									disabled={connecting || !formName.trim() || !formBootstrap.trim()}
									class="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 disabled:bg-surface-700 disabled:text-surface-500 text-white font-mono text-sm rounded transition-colors"
								>
									{connecting ? 'connecting...' : 'connect'}
								</button>
								<button
									type="button"
									onclick={() => showForm = false}
									class="px-3 py-1.5 bg-surface-700 hover:bg-surface-600 text-surface-300 font-mono text-sm rounded transition-colors"
								>
									cancel
								</button>
							</div>
						</form>
					</div>
				{/if}

				<!-- Saved clusters -->
				{#if clusters.length > 0 && !showForm}
					<div class="border-t border-surface-700">
						<div class="px-4 py-2 bg-surface-900/50 text-xs font-mono text-surface-500">
							saved clusters ({clusters.length})
						</div>
						{#each clusters as cluster}
							<div class="flex items-center justify-between px-4 py-2 border-t border-surface-700/50 hover:bg-surface-700/30">
								<div class="font-mono text-sm">
									<span class="text-surface-200">{cluster.name}</span>
									<span class="text-surface-500 ml-2 text-xs">{cluster.bootstrap_servers}</span>
								</div>
								<button
									type="button"
									onclick={() => handleConnect(cluster)}
									disabled={connecting}
									class="px-2 py-0.5 text-xs font-mono bg-emerald-600/20 text-emerald-400 hover:bg-emerald-600/30 rounded border border-emerald-600/50 disabled:opacity-50"
								>
									connect
								</button>
							</div>
						{/each}
					</div>
				{/if}
			</section>

		</div>
	</div>
</div>
