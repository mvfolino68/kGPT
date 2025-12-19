<script lang="ts">
	import { SettingsCard, FormField } from '$lib/components/settings';
	import type { KafkaCluster, ClusterInfo } from '$lib/api';

	interface Props {
		clusterInfo: Partial<ClusterInfo> & { connected: boolean };
		clusters: KafkaCluster[];
		loading: boolean;
		connecting: boolean;
		error: string | null;
		showForm: boolean;
		formName: string;
		formBootstrap: string;
		formProtocol: string;
		onconnect: (cluster?: KafkaCluster) => void;
		ondisconnect: () => void;
		onconnectdemo: () => void;
		onshowform: () => void;
		onhideform: () => void;
		onformnamechange: (value: string) => void;
		onformbootstrapchange: (value: string) => void;
		onformprotocolchange: (value: string) => void;
	}

	let {
		clusterInfo,
		clusters,
		loading,
		connecting,
		error,
		showForm,
		formName,
		formBootstrap,
		formProtocol,
		onconnect,
		ondisconnect,
		onconnectdemo,
		onshowform,
		onhideform,
		onformnamechange,
		onformbootstrapchange,
		onformprotocolchange
	}: Props = $props();
</script>

<SettingsCard
	title="Kafka Cluster"
	status={clusterInfo.connected ? 'connected' : null}
	variant={clusterInfo.connected ? 'success' : 'default'}
>
	{#snippet icon()}
		<svg class="w-4 h-4 {clusterInfo.connected ? 'text-emerald-400' : 'text-surface-500'}" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
			<path stroke-linecap="round" stroke-linejoin="round" d="M5.25 14.25h13.5m-13.5 0a3 3 0 01-3-3m3 3a3 3 0 100 6h13.5a3 3 0 100-6m-16.5-3a3 3 0 013-3h13.5a3 3 0 013 3m-19.5 0a4.5 4.5 0 01.9-2.7L5.737 5.1a3.375 3.375 0 012.7-1.35h7.126c1.062 0 2.062.5 2.7 1.35l2.587 3.45a4.5 4.5 0 01.9 2.7m0 0a3 3 0 01-3 3m0 3h.008v.008h-.008v-.008zm0-6h.008v.008h-.008v-.008zm-3 6h.008v.008h-.008v-.008zm0-6h.008v.008h-.008v-.008z" />
		</svg>
	{/snippet}

	{#snippet headerAction()}
		{#if loading}
			<span class="text-xs text-surface-500">Loading...</span>
		{:else if clusterInfo.connected}
			<button
				type="button"
				class="text-xs text-primary-light hover:text-primary transition-colors"
				onclick={ondisconnect}
			>
				Disconnect
			</button>
		{/if}
	{/snippet}

	<div class="space-y-4">
		{#if error}
			<div class="flex items-center gap-2 text-sm text-red-400 bg-red-500/10 rounded-lg px-3 py-2">
				<svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
				</svg>
				<span>{error}</span>
			</div>
		{/if}

		{#if clusterInfo.connected}
			<div>
				<p class="text-sm font-medium text-surface-100">{clusterInfo.cluster_id || 'Connected Cluster'}</p>
				<p class="text-xs text-surface-500 mt-0.5">
					{clusterInfo.brokers || 0} broker(s) | {clusterInfo.topics?.length || 0} topics
				</p>
			</div>
		{:else if showForm}
			<form onsubmit={(e) => { e.preventDefault(); onconnect(); }} class="space-y-4">
				<div class="grid grid-cols-2 gap-3">
					<FormField label="Name" id="cluster-name">
						<input
							id="cluster-name"
							type="text"
							value={formName}
							oninput={(e) => onformnamechange(e.currentTarget.value)}
							placeholder="my-cluster"
							class="w-full input"
						/>
					</FormField>
					<FormField label="Protocol" id="cluster-protocol">
						<select
							id="cluster-protocol"
							value={formProtocol}
							onchange={(e) => onformprotocolchange(e.currentTarget.value)}
							class="w-full input"
						>
							<option value="PLAINTEXT">PLAINTEXT</option>
							<option value="SSL">SSL</option>
							<option value="SASL_PLAINTEXT">SASL_PLAINTEXT</option>
							<option value="SASL_SSL">SASL_SSL</option>
						</select>
					</FormField>
				</div>
				<FormField label="Bootstrap Servers" id="cluster-bootstrap">
					<input
						id="cluster-bootstrap"
						type="text"
						value={formBootstrap}
						oninput={(e) => onformbootstrapchange(e.currentTarget.value)}
						placeholder="localhost:9092"
						class="w-full input"
					/>
				</FormField>
				<div class="flex gap-2 justify-end pt-2">
					<button type="button" class="btn btn-ghost" onclick={onhideform}>
						Cancel
					</button>
					<button
						type="submit"
						class="btn btn-primary"
						disabled={connecting || !formName.trim() || !formBootstrap.trim()}
					>
						{connecting ? 'Connecting...' : 'Connect'}
					</button>
				</div>
			</form>
		{:else}
			<div class="space-y-2">
				<button
					type="button"
					class="w-full p-3 rounded-lg bg-surface-800/50 border border-surface-700/50 hover:border-emerald-500/30 hover:bg-surface-800 transition-all text-left group"
					onclick={onconnectdemo}
				>
					<div class="flex items-center gap-3">
						<div class="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center">
							<svg class="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
								<path stroke-linecap="round" stroke-linejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347a1.125 1.125 0 01-1.667-.985V5.653z" />
							</svg>
						</div>
						<div class="flex-1">
							<span class="text-sm font-medium text-surface-100 group-hover:text-emerald-400 transition-colors">Demo Cluster</span>
							<p class="text-xs text-surface-500">localhost:9094</p>
						</div>
						<svg class="w-4 h-4 text-surface-600 group-hover:text-emerald-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
							<path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
						</svg>
					</div>
				</button>
				<button
					type="button"
					class="w-full p-3 rounded-lg bg-surface-800/50 border border-surface-700/50 hover:border-primary/30 hover:bg-surface-800 transition-all text-left group"
					onclick={onshowform}
				>
					<div class="flex items-center gap-3">
						<div class="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
							<svg class="w-4 h-4 text-primary-light" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
								<path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
							</svg>
						</div>
						<div class="flex-1">
							<span class="text-sm font-medium text-surface-100 group-hover:text-primary-light transition-colors">Custom Cluster</span>
							<p class="text-xs text-surface-500">Enter connection details</p>
						</div>
						<svg class="w-4 h-4 text-surface-600 group-hover:text-primary-light transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
							<path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
						</svg>
					</div>
				</button>

				{#if clusters.length > 0}
					<div class="pt-3 mt-2 border-t border-surface-700/50">
						<p class="text-[11px] font-medium uppercase tracking-wider text-surface-500 mb-2">Saved Clusters</p>
						<div class="space-y-1.5">
							{#each clusters as cluster}
								<button
									type="button"
									class="w-full p-2.5 rounded-lg bg-surface-800/30 border border-surface-700/50 hover:border-primary/30 hover:bg-surface-800 transition-all text-left group"
									onclick={() => onconnect(cluster)}
									disabled={connecting}
								>
									<div class="flex items-center justify-between">
										<div>
											<span class="text-sm text-surface-200 group-hover:text-primary-light transition-colors">{cluster.name}</span>
											<p class="text-xs text-surface-500">{cluster.bootstrap_servers}</p>
										</div>
										<svg class="w-4 h-4 text-surface-600 group-hover:text-primary-light transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
											<path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
										</svg>
									</div>
								</button>
							{/each}
						</div>
					</div>
				{/if}
			</div>
		{/if}
	</div>
</SettingsCard>
