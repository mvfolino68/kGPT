<script lang="ts">
	import { Button, Icon, LoadingState, ActionCard } from '$lib/components/ui';
	import { SettingsCard } from '$lib/components/settings';
	import type { KafkaCluster, ClusterInfo } from '$lib/api';
	import KafkaCurrentConnection from './KafkaCurrentConnection.svelte';
	import KafkaConnectionForm from './KafkaConnectionForm.svelte';
	import KafkaSavedClusters from './KafkaSavedClusters.svelte';
	import KafkaLogViewer from './KafkaLogViewer.svelte';

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
		ondelete: (clusterId: number) => void;
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
		onformprotocolchange,
		ondelete
	}: Props = $props();

	let showLogs = $state(false);
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
			<KafkaCurrentConnection {clusterInfo} />
		{/if}

		{#if showForm}
			<KafkaConnectionForm
				name={formName}
				bootstrap={formBootstrap}
				protocol={formProtocol}
				{connecting}
				onnamechange={onformnamechange}
				onbootstrapchange={onformbootstrapchange}
				onprotocolchange={onformprotocolchange}
				onconnect={onconnect}
				oncancel={onhideform}
			/>
		{:else}
			<div class="grid grid-cols-2 gap-3">
				<ActionCard
					icon="play"
					title="Demo Cluster"
					description="localhost:9094"
					onclick={onconnectdemo}
					variant="primary"
				/>
				<ActionCard
					icon="plus"
					title="Custom Cluster"
					description="Add new connection"
					onclick={onshowform}
				/>
			</div>

			{#if clusters.length > 0}
				<KafkaSavedClusters
					{clusters}
					{connecting}
					onconnect={onconnect}
					ondisconnect={ondisconnect}
					ondelete={ondelete}
				/>
			{/if}
		{/if}


		<!-- Debug Logs -->
		<div class="pt-4 border-t border-border">
			<button
				class="flex items-center gap-2 text-sm text-text-secondary hover:text-text transition-colors w-full"
				onclick={() => showLogs = !showLogs}
			>
				<Icon name={showLogs ? 'chevron-down' : 'chevron-right'} size="sm" />
				<span class="font-medium">Debug Logs</span>
			</button>

			{#if showLogs}
				<div class="mt-3">
					<KafkaLogViewer />
				</div>
			{/if}
		</div>
	</div>
</SettingsCard>
