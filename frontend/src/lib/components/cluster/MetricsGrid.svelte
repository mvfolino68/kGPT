<script lang="ts">
	import { Icon } from '$lib/components/ui';

	interface Props {
		brokers: number;
		topics: number;
		consumerGroups: number;
		connected: boolean;
		clusterId?: string;
	}

	let { brokers, topics, consumerGroups, connected, clusterId }: Props = $props();
</script>

<div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
	<!-- Connection Status -->
	<div class="col-span-2 lg:col-span-1 bg-surface rounded-lg p-4">
		<div class="flex items-center gap-3 mb-3">
			<div class="w-10 h-10 rounded-lg bg-surface-hover flex items-center justify-center">
				{#if connected}
					<Icon name="check" size="md" class="text-success" />
				{:else}
					<Icon name="x" size="md" class="text-text-tertiary" />
				{/if}
			</div>
			<div>
				<p class="label">Status</p>
				<p class="text-lg font-semibold {connected ? 'text-success' : 'text-text-tertiary'}">
					{connected ? 'Connected' : 'Disconnected'}
				</p>
			</div>
		</div>
		{#if clusterId}
			<p class="text-xs text-text-tertiary font-mono truncate" title={clusterId}>
				{clusterId}
			</p>
		{/if}
	</div>

	<!-- Brokers -->
	<div class="bg-surface rounded-lg p-4">
		<div class="flex items-center gap-3">
			<div class="w-10 h-10 rounded-lg bg-surface-hover flex items-center justify-center">
				<Icon name="server" size="md" class="text-text-secondary" />
			</div>
			<div>
				<p class="label">Brokers</p>
				<p class="text-2xl font-bold text-text tabular-nums">{brokers}</p>
			</div>
		</div>
	</div>

	<!-- Topics -->
	<div class="bg-surface rounded-lg p-4">
		<div class="flex items-center gap-3">
			<div class="w-10 h-10 rounded-lg bg-surface-hover flex items-center justify-center">
				<Icon name="folder" size="md" class="text-text-secondary" />
			</div>
			<div>
				<p class="label">Topics</p>
				<p class="text-2xl font-bold text-text tabular-nums">{topics}</p>
			</div>
		</div>
	</div>

	<!-- Consumer Groups -->
	<div class="bg-surface rounded-lg p-4">
		<div class="flex items-center gap-3">
			<div class="w-10 h-10 rounded-lg bg-surface-hover flex items-center justify-center">
				<Icon name="users" size="md" class="text-text-secondary" />
			</div>
			<div>
				<p class="label">Consumer Groups</p>
				<p class="text-2xl font-bold text-text tabular-nums">{consumerGroups}</p>
			</div>
		</div>
	</div>
</div>
