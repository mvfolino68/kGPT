<script lang="ts">
	import { Button, Input, Select, Icon, LoadingState } from '$lib/components/ui';
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

	let nameValue = $state('');
	let bootstrapValue = $state('');
	let protocolValue = $state('PLAINTEXT');

	$effect(() => { nameValue = formName; });
	$effect(() => { bootstrapValue = formBootstrap; });
	$effect(() => { protocolValue = formProtocol; });

	const protocolOptions = [
		{ value: 'PLAINTEXT', label: 'PLAINTEXT' },
		{ value: 'SSL', label: 'SSL' },
		{ value: 'SASL_PLAINTEXT', label: 'SASL_PLAINTEXT' },
		{ value: 'SASL_SSL', label: 'SASL_SSL' }
	];
</script>

<SettingsCard
	title="Kafka Cluster"
	status={clusterInfo.connected ? 'connected' : null}
>
	{#snippet icon()}
		<Icon name="server" size="sm" class="text-text-tertiary" />
	{/snippet}

	{#snippet headerAction()}
		{#if loading}
			<LoadingState message="Loading..." showSpinner={false} size="xs" class="text-text-tertiary" />
		{:else if clusterInfo.connected}
			<Button variant="danger" size="sm" onclick={ondisconnect}>
				Disconnect
			</Button>
		{/if}
	{/snippet}

	<div class="space-y-6">
		{#if error}
			<div class="flex items-center gap-2 text-sm text-error bg-error-bg rounded-lg px-3 py-2">
				<Icon name="error" size="sm" />
				<span>{error}</span>
			</div>
		{/if}

		{#if clusterInfo.connected}
			<div class="bg-surface-800/50 rounded-lg p-4 border border-surface-700/50">
				<div class="flex items-center justify-between mb-2">
					<span class="text-xs font-bold uppercase tracking-wider text-surface-400">Current Connection</span>
					<div class="flex items-center gap-2">
						<span class="relative flex h-2 w-2">
						  <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
						  <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
						</span>
						<span class="text-xs text-emerald-500 font-medium">Connected</span>
					</div>
				</div>
				<div>
					<p class="text-sm font-medium text-text">{clusterInfo.cluster_id || 'Connected Cluster'}</p>
					<p class="text-xs text-text-tertiary mt-0.5">
						{clusterInfo.brokers || 0} broker(s) | {clusterInfo.topics?.length || 0} topics
					</p>
				</div>
			</div>
		{/if}

		{#if showForm}
			<div class="bg-surface-800/50 rounded-lg p-4 border border-surface-700/50">
				<div class="mb-4">
					<span class="text-xs font-bold uppercase tracking-wider text-surface-400">New Connection</span>
				</div>
				<form onsubmit={(e) => { e.preventDefault(); onconnect(); }} class="space-y-4">
					<div class="grid grid-cols-2 gap-3">
						<FormField label="Name" id="cluster-name">
							<Input
								id="cluster-name"
								type="text"
								bind:value={nameValue}
								oninput={(e) => onformnamechange((e.target as HTMLInputElement).value)}
								placeholder="my-cluster"
							/>
						</FormField>
						<FormField label="Protocol" id="cluster-protocol">
							<Select
								id="cluster-protocol"
								bind:value={protocolValue}
								options={protocolOptions}
								onchange={() => onformprotocolchange(protocolValue)}
							/>
						</FormField>
					</div>
					<FormField label="Bootstrap Servers" id="cluster-bootstrap">
						<Input
							id="cluster-bootstrap"
							type="text"
							bind:value={bootstrapValue}
							oninput={(e) => onformbootstrapchange((e.target as HTMLInputElement).value)}
							placeholder="localhost:9092"
						/>
					</FormField>
					<div class="flex gap-2 justify-end pt-2">
						<Button type="button" variant="ghost" onclick={onhideform}>
							Cancel
						</Button>
						<Button
							type="submit"
							variant="primary"
							disabled={connecting || !nameValue.trim() || !bootstrapValue.trim()}
							loading={connecting}
						>
							Connect
						</Button>
					</div>
				</form>
			</div>
		{:else}
			<div class="grid grid-cols-2 gap-3">
				<Button
					variant="secondary"
					size="lg"
					class="justify-start text-left h-auto py-3"
					onclick={onconnectdemo}
				>
					<div class="flex items-center gap-3">
						<div class="w-8 h-8 rounded-lg bg-surface flex items-center justify-center shrink-0">
							<Icon name="play" size="sm" class="text-text-secondary" />
						</div>
						<div class="min-w-0">
							<span class="text-sm font-medium block">Demo Cluster</span>
							<span class="text-xs text-text-tertiary block truncate">localhost:9094</span>
						</div>
					</div>
				</Button>
				<Button
					variant="secondary"
					size="lg"
					class="justify-start text-left h-auto py-3"
					onclick={onshowform}
				>
					<div class="flex items-center gap-3">
						<div class="w-8 h-8 rounded-lg bg-surface flex items-center justify-center shrink-0">
							<Icon name="plus" size="sm" class="text-text-secondary" />
						</div>
						<div class="min-w-0">
							<span class="text-sm font-medium block">Custom Cluster</span>
							<span class="text-xs text-text-tertiary block truncate">Add new connection</span>
						</div>
					</div>
				</Button>
			</div>

			{#if clusters.length > 0}
				<div class="pt-2">
					<div class="flex items-center justify-between mb-3 px-1">
						<span class="text-xs font-bold uppercase tracking-wider text-surface-400">Saved Clusters</span>
					</div>
					<div class="space-y-2">
						{#each clusters as cluster}
							<div class="group flex items-center gap-2 p-3 bg-surface-800/30 hover:bg-surface-800/80 border border-transparent hover:border-surface-700/50 rounded-lg transition-all duration-200">
								<div class="w-2 h-2 rounded-full {cluster.is_active ? 'bg-emerald-500 shadow-sm shadow-emerald-500/50' : 'bg-surface-600'} shrink-0"></div>
								<div class="flex-1 min-w-0 grid gap-0.5">
									<span class="text-sm font-medium text-surface-200 truncate">{cluster.name}</span>
									<span class="text-xs text-surface-500 font-mono truncate">{cluster.bootstrap_servers}</span>
								</div>

								<div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
									{#if !cluster.is_active}
										<Button
											variant="ghost"
											size="sm"
											class="h-7 px-2 text-xs"
											onclick={() => onconnect(cluster)}
											disabled={connecting}
										>
											Connect
										</Button>
									{:else}
										<Button
											variant="ghost"
											size="sm"
											class="h-7 px-2 text-xs text-red-400 hover:text-red-300 hover:bg-red-400/10"
											onclick={ondisconnect}
										>
											Disconnect
										</Button>
									{/if}
								</div>
							</div>
						{/each}
					</div>
				</div>
			{/if}
		{/if}
	</div>
</SettingsCard>
