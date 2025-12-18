<script lang="ts">
	import { Card, StatusDot } from '$lib/components/ui';

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
	<Card class="col-span-2 lg:col-span-1">
		<div class="flex items-center gap-3 mb-3">
			<div class="w-10 h-10 rounded-lg bg-surface-700/50 flex items-center justify-center">
				{#if connected}
					<svg class="w-5 h-5 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
					</svg>
				{:else}
					<svg class="w-5 h-5 text-surface-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
					</svg>
				{/if}
			</div>
			<div>
				<p class="text-xs text-surface-500 uppercase tracking-wider">Status</p>
				<p class="text-lg font-semibold {connected ? 'text-success' : 'text-surface-400'}">
					{connected ? 'Connected' : 'Disconnected'}
				</p>
			</div>
		</div>
		{#if clusterId}
			<p class="text-xs text-surface-500 font-mono truncate" title={clusterId}>
				{clusterId}
			</p>
		{/if}
	</Card>

	<!-- Brokers -->
	<Card>
		<div class="flex items-center gap-3">
			<div class="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
				<svg class="w-5 h-5 text-primary-light" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
				</svg>
			</div>
			<div>
				<p class="text-xs text-surface-500 uppercase tracking-wider">Brokers</p>
				<p class="text-2xl font-bold text-surface-100 tabular-nums">{brokers}</p>
			</div>
		</div>
	</Card>

	<!-- Topics -->
	<Card>
		<div class="flex items-center gap-3">
			<div class="w-10 h-10 rounded-lg bg-purple-500/10 flex items-center justify-center">
				<svg class="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
				</svg>
			</div>
			<div>
				<p class="text-xs text-surface-500 uppercase tracking-wider">Topics</p>
				<p class="text-2xl font-bold text-surface-100 tabular-nums">{topics}</p>
			</div>
		</div>
	</Card>

	<!-- Consumer Groups -->
	<Card>
		<div class="flex items-center gap-3">
			<div class="w-10 h-10 rounded-lg bg-amber-500/10 flex items-center justify-center">
				<svg class="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
				</svg>
			</div>
			<div>
				<p class="text-xs text-surface-500 uppercase tracking-wider">Consumer Groups</p>
				<p class="text-2xl font-bold text-surface-100 tabular-nums">{consumerGroups}</p>
			</div>
		</div>
	</Card>
</div>
