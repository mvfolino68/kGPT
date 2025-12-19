<script lang="ts">
	import { Button } from '$lib/components/ui';
	import WizardStep from '../WizardStep.svelte';
	import { connectCluster, getClusterInfo, type ClusterInfo } from '$lib/api';
	import { StatusIndicator } from '$lib/components';

	interface Props {
		onNext: () => void;
		onBack: () => void;
		onSkip: () => void;
	}

	let { onNext, onBack, onSkip }: Props = $props();

	let mode = $state<'choice' | 'demo' | 'custom'>('choice');
	let connecting = $state(false);
	let connected = $state(false);
	let error = $state<string | null>(null);
	let clusterInfo = $state<Partial<ClusterInfo> | null>(null);

	// Custom cluster form
	let clusterName = $state('');
	let bootstrapServers = $state('');
	let securityProtocol = $state('PLAINTEXT');

	async function connectDemo() {
		mode = 'demo';
		connecting = true;
		error = null;

		try {
			await connectCluster({
				name: 'Demo Cluster',
				bootstrap_servers: 'localhost:9094',
				security_protocol: 'PLAINTEXT'
			});
			const info = await getClusterInfo();
			clusterInfo = info;
			connected = info.connected;
			if (!info.connected) {
				error = 'Demo cluster not available. Make sure Docker is running with "make dev".';
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Connection failed';
		} finally {
			connecting = false;
		}
	}

	async function connectCustom() {
		if (!clusterName.trim() || !bootstrapServers.trim()) return;

		connecting = true;
		error = null;

		try {
			await connectCluster({
				name: clusterName.trim(),
				bootstrap_servers: bootstrapServers.trim(),
				security_protocol: securityProtocol
			});
			const info = await getClusterInfo();
			clusterInfo = info;
			connected = info.connected;
			if (!info.connected) {
				error = 'Failed to connect. Check your bootstrap servers.';
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Connection failed';
		} finally {
			connecting = false;
		}
	}

	function showCustomForm() {
		mode = 'custom';
		error = null;
	}

	function goBack() {
		if (mode === 'choice') {
			onBack();
		} else {
			mode = 'choice';
			error = null;
			connected = false;
		}
	}
</script>

<WizardStep
	title="Connect Kafka Cluster"
	subtitle="Connect to a cluster or skip for now"
>
	{#snippet children()}
		<div class="max-w-sm mx-auto">
			{#if mode === 'choice'}
				<!-- Initial choice -->
				<div class="space-y-3">
					<Button
						variant="secondary"
						size="lg"
						class="w-full justify-start text-left p-4 rounded-lg bg-surface-800/50 border border-surface-700/50 hover:border-primary/50 hover:bg-surface-800 group"
						onclick={connectDemo}
					>
						<div class="flex items-center gap-4">
							<div class="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
								<svg class="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
									<path stroke-linecap="round" stroke-linejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347a1.125 1.125 0 01-1.667-.985V5.653z" />
								</svg>
							</div>
							<div class="flex-1">
								<h3 class="text-sm font-medium text-surface-100 group-hover:text-primary-light">Use Demo Cluster</h3>
								<p class="text-xs text-surface-500 mt-0.5">Connect to the local development cluster</p>
							</div>
							<svg class="w-5 h-5 text-surface-600 group-hover:text-primary-light" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
								<path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
							</svg>
						</div>
					</Button>

					<Button
						variant="secondary"
						size="lg"
						class="w-full justify-start text-left p-4 rounded-lg bg-surface-800/50 border border-surface-700/50 hover:border-primary/50 hover:bg-surface-800 group"
						onclick={showCustomForm}
					>
						<div class="flex items-center gap-4">
							<div class="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
								<svg class="w-6 h-6 text-primary-light" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
									<path stroke-linecap="round" stroke-linejoin="round" d="M5.25 14.25h13.5m-13.5 0a3 3 0 01-3-3m3 3a3 3 0 100 6h13.5a3 3 0 100-6m-16.5-3a3 3 0 013-3h13.5a3 3 0 013 3m-19.5 0a4.5 4.5 0 01.9-2.7L5.737 5.1a3.375 3.375 0 012.7-1.35h7.126c1.062 0 2.062.5 2.7 1.35l2.587 3.45a4.5 4.5 0 01.9 2.7m0 0a3 3 0 01-3 3m0 3h.008v.008h-.008v-.008zm0-6h.008v.008h-.008v-.008zm-3 6h.008v.008h-.008v-.008zm0-6h.008v.008h-.008v-.008z" />
								</svg>
							</div>
							<div class="flex-1">
								<h3 class="text-sm font-medium text-surface-100 group-hover:text-primary-light">Connect Custom Cluster</h3>
								<p class="text-xs text-surface-500 mt-0.5">Enter your own cluster details</p>
							</div>
							<svg class="w-5 h-5 text-surface-600 group-hover:text-primary-light" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
								<path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
							</svg>
						</div>
					</Button>
				</div>

			{:else if mode === 'demo'}
				<!-- Demo cluster connection -->
				<div class="space-y-4">
					{#if connecting}
						<div class="text-center py-8">
							<svg class="w-8 h-8 mx-auto text-primary animate-spin mb-4" fill="none" viewBox="0 0 24 24">
								<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
								<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
							</svg>
							<p class="text-surface-400 text-sm">Connecting to demo cluster...</p>
						</div>
					{:else if connected}
						<div class="p-4 rounded-lg bg-success-bg border border-success/30">
							<div class="flex items-center gap-3 mb-3">
								<StatusIndicator status="active" size="sm" />
								<span class="text-sm font-medium text-success">Connected</span>
							</div>
							<div class="text-xs text-surface-400 space-y-1">
								<p>Cluster: {clusterInfo?.cluster_id || 'Demo Cluster'}</p>
								<p>Brokers: {clusterInfo?.brokers || 1}</p>
								<p>Topics: {clusterInfo?.topics?.length || 0}</p>
							</div>
						</div>
					{:else if error}
						<div class="p-4 rounded-lg bg-error-bg border border-error/30">
							<div class="flex items-center gap-2 text-sm text-error">
								<StatusIndicator status="error" size="sm" />
								<span>{error}</span>
							</div>
						</div>
						<Button variant="default" class="w-full" onclick={connectDemo}>
							Retry
						</Button>
					{/if}
				</div>

			{:else if mode === 'custom'}
				<!-- Custom cluster form -->
				<div class="space-y-4">
					{#if connected}
						<div class="p-4 rounded-lg bg-success-bg border border-success/30">
							<div class="flex items-center gap-3 mb-3">
								<StatusIndicator status="active" size="sm" />
								<span class="text-sm font-medium text-success">Connected</span>
							</div>
							<div class="text-xs text-surface-400 space-y-1">
								<p>Cluster: {clusterInfo?.cluster_id || clusterName}</p>
								<p>Brokers: {clusterInfo?.brokers || 0}</p>
							</div>
						</div>
					{:else}
						<div>
							<label for="cluster-name" class="block text-xs font-medium uppercase tracking-wider text-surface-500 mb-2">
								Cluster Name
							</label>
							<input
								id="cluster-name"
								type="text"
								bind:value={clusterName}
								placeholder="My Cluster"
								class="w-full bg-surface-700/50 border-none rounded-md px-3 py-2 text-sm text-foreground placeholder:text-muted transition-all focus:outline-none focus:bg-surface-700 focus:ring-2 focus:ring-primary-600/50"
							/>
						</div>

						<div>
							<label for="bootstrap" class="block text-xs font-medium uppercase tracking-wider text-surface-500 mb-2">
								Bootstrap Servers
							</label>
							<input
								id="bootstrap"
								type="text"
								bind:value={bootstrapServers}
								placeholder="localhost:9092"
								class="w-full bg-surface-700/50 border-none rounded-md px-3 py-2 text-sm text-foreground placeholder:text-muted transition-all focus:outline-none focus:bg-surface-700 focus:ring-2 focus:ring-primary-600/50"
							/>
						</div>

						<div>
							<label for="protocol" class="block text-xs font-medium uppercase tracking-wider text-surface-500 mb-2">
								Security Protocol
							</label>
							<select id="protocol" bind:value={securityProtocol} class="w-full input">
								<option value="PLAINTEXT">PLAINTEXT</option>
								<option value="SSL">SSL</option>
								<option value="SASL_PLAINTEXT">SASL_PLAINTEXT</option>
								<option value="SASL_SSL">SASL_SSL</option>
							</select>
						</div>

						{#if error}
							<div class="flex items-center gap-2 text-sm text-error">
								<StatusIndicator status="error" size="sm" />
								<span>{error}</span>
							</div>
						{/if}

						<Button
							variant="primary"
							class="w-full"
							onclick={connectCustom}
							disabled={connecting || !clusterName.trim() || !bootstrapServers.trim()}
							loading={connecting}
						>
							Connect
						</Button>
					{/if}
				</div>
			{/if}
		</div>
	{/snippet}

	{#snippet actions()}
		<div class="flex justify-between">
			<Button variant="ghost" onclick={goBack}>
				Back
			</Button>
			<div class="flex gap-3">
				{#if !connected}
					<Button variant="ghost" onclick={onSkip}>
						Skip for now
					</Button>
				{/if}
				{#if connected}
					<Button variant="primary" class="px-6" onclick={onNext}>
						Continue
					</Button>
				{/if}
			</div>
		</div>
	{/snippet}
</WizardStep>
