<script lang="ts">
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
	<div class="col-span-2 lg:col-span-1 bg-surface-800 rounded-lg p-4">
		<div class="flex items-center gap-3 mb-3">
			<div class="w-10 h-10 rounded-lg bg-surface-700/50 flex items-center justify-center">
				{#if connected}
					<svg class="w-5 h-5 text-emerald-400/80" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
					</svg>
				{:else}
					<svg class="w-5 h-5 text-surface-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
					</svg>
				{/if}
			</div>
			<div>
				<p class="text-[10px] font-bold uppercase tracking-wider text-surface-500">Status</p>
				<p class="text-lg font-semibold {connected ? 'text-emerald-400/80' : 'text-surface-400'}">
					{connected ? 'Connected' : 'Disconnected'}
				</p>
			</div>
		</div>
		{#if clusterId}
			<p class="text-xs text-surface-500 font-mono truncate" title={clusterId}>
				{clusterId}
			</p>
		{/if}
	</div>

	<!-- Brokers -->
	<div class="bg-surface-800 rounded-lg p-4">
		<div class="flex items-center gap-3">
			<div class="w-10 h-10 rounded-lg bg-surface-700/50 flex items-center justify-center">
				<svg class="w-5 h-5 text-surface-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
				</svg>
			</div>
			<div>
				<p class="text-[10px] font-bold uppercase tracking-wider text-surface-500">Brokers</p>
				<p class="text-2xl font-bold text-surface-100 tabular-nums">{brokers}</p>
			</div>
		</div>
	</div>

	<!-- Topics -->
	<div class="bg-surface-800 rounded-lg p-4">
		<div class="flex items-center gap-3">
			<div class="w-10 h-10 rounded-lg bg-surface-700/50 flex items-center justify-center">
				<svg class="w-5 h-5 text-surface-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
				</svg>
			</div>
			<div>
				<p class="text-[10px] font-bold uppercase tracking-wider text-surface-500">Topics</p>
				<p class="text-2xl font-bold text-surface-100 tabular-nums">{topics}</p>
			</div>
		</div>
	</div>

	<!-- Consumer Groups -->
	<div class="bg-surface-800 rounded-lg p-4">
		<div class="flex items-center gap-3">
			<div class="w-10 h-10 rounded-lg bg-surface-700/50 flex items-center justify-center">
				<svg class="w-5 h-5 text-surface-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
				</svg>
			</div>
			<div>
				<p class="text-[10px] font-bold uppercase tracking-wider text-surface-500">Consumer Groups</p>
				<p class="text-2xl font-bold text-surface-100 tabular-nums">{consumerGroups}</p>
			</div>
		</div>
	</div>
</div>
