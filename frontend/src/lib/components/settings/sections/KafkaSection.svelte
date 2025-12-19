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

	<div class="space-y-4">
		{#if error}
			<div class="flex items-center gap-2 text-sm text-error bg-error-bg rounded-lg px-3 py-2">
				<Icon name="error" size="sm" />
				<span>{error}</span>
			</div>
		{/if}

		{#if clusterInfo.connected}
			<div>
				<p class="text-sm font-medium text-text">{clusterInfo.cluster_id || 'Connected Cluster'}</p>
				<p class="text-xs text-text-tertiary mt-0.5">
					{clusterInfo.brokers || 0} broker(s) | {clusterInfo.topics?.length || 0} topics
				</p>
			</div>
		{:else if showForm}
			<form onsubmit={(e) => { e.preventDefault(); onconnect(); }} class="space-y-4">
				<div class="grid grid-cols-2 gap-3">
					<FormField label="Name" id="cluster-name">
						<Input
							id="cluster-name"
							type="text"
							bind:value={nameValue}
							oninput={() => onformnamechange(nameValue)}
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
						oninput={() => onformbootstrapchange(bootstrapValue)}
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
		{:else}
			<div class="space-y-2">
				<Button
					variant="secondary"
					size="lg"
					class="w-full justify-start text-left"
					onclick={onconnectdemo}
				>
					<div class="flex items-center gap-3">
						<div class="w-8 h-8 rounded-lg bg-surface flex items-center justify-center">
							<Icon name="play" size="sm" class="text-text-secondary" />
						</div>
						<div class="flex-1">
							<span class="text-sm font-medium">Demo Cluster</span>
							<p class="text-xs text-text-tertiary">localhost:9094</p>
						</div>
						<Icon name="chevron-right" size="sm" class="text-text-tertiary" />
					</div>
				</Button>
				<Button
					variant="secondary"
					size="lg"
					class="w-full justify-start text-left"
					onclick={onshowform}
				>
					<div class="flex items-center gap-3">
						<div class="w-8 h-8 rounded-lg bg-surface flex items-center justify-center">
							<Icon name="plus" size="sm" class="text-text-secondary" />
						</div>
						<div class="flex-1">
							<span class="text-sm font-medium">Custom Cluster</span>
							<p class="text-xs text-text-tertiary">Enter connection details</p>
						</div>
						<Icon name="chevron-right" size="sm" class="text-text-tertiary" />
					</div>
				</Button>

				{#if clusters.length > 0}
					<div class="pt-3 mt-2">
						<p class="label mb-2">Saved Clusters</p>
						<div class="space-y-1.5">
							{#each clusters as cluster}
								<Button
									variant="secondary"
									size="md"
									class="w-full justify-start text-left"
									onclick={() => onconnect(cluster)}
									disabled={connecting}
								>
									<div class="flex items-center justify-between w-full">
										<div>
											<span class="text-sm">{cluster.name}</span>
											<p class="text-xs text-text-tertiary">{cluster.bootstrap_servers}</p>
										</div>
										<Icon name="chevron-right" size="sm" class="text-text-tertiary" />
									</div>
								</Button>
							{/each}
						</div>
					</div>
				{/if}
			</div>
		{/if}
	</div>
</SettingsCard>
