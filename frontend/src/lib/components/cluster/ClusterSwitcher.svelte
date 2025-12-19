<script lang="ts">
	import { getClusters, connectCluster, disconnectCluster, type KafkaCluster } from '$lib/api';
	import { onMount } from 'svelte';
	import { Button, Icon } from '$lib/components/ui';
	import { fly } from 'svelte/transition';

	interface Props {
		currentClusterId?: string | null;
		onSwitch?: () => void;
	}

	let { currentClusterId, onSwitch }: Props = $props();

	let clusters = $state<KafkaCluster[]>([]);
	let isOpen = $state(false);
	let loading = $state(false);
	let switchingTo = $state<number | null>(null);

	async function loadClusters() {
		try {
			clusters = await getClusters();
		} catch (e) {
			console.error('Failed to load clusters:', e);
		}
	}

	async function handleSwitch(cluster: KafkaCluster) {
		if (cluster.is_active) {
			isOpen = false;
			return;
		}

		switchingTo = cluster.id;
		try {
			await connectCluster({
				name: cluster.name,
				bootstrap_servers: cluster.bootstrap_servers,
				security_protocol: cluster.security_protocol
			});
			await loadClusters();
			onSwitch?.();
		} catch (e) {
			console.error('Failed to switch cluster:', e);
		} finally {
			switchingTo = null;
			isOpen = false;
		}
	}

	async function handleDisconnect() {
		loading = true;
		try {
			await disconnectCluster();
			await loadClusters();
			onSwitch?.();
		} catch (e) {
			console.error('Failed to disconnect:', e);
		} finally {
			loading = false;
			isOpen = false;
		}
	}

	function handleClickOutside(e: MouseEvent) {
		const target = e.target as HTMLElement;
		if (!target.closest('.cluster-switcher')) {
			isOpen = false;
		}
	}

	onMount(() => {
		loadClusters();
		document.addEventListener('click', handleClickOutside);
		return () => document.removeEventListener('click', handleClickOutside);
	});

	const activeCluster = $derived(clusters.find((c) => c.is_active));
</script>

{#if clusters.length > 0}
	<div class="cluster-switcher relative">
		<Button
			variant="ghost"
			size="sm"
			class="hover:bg-surface-800 border border-transparent hover:border-surface-700/50 transition-all duration-200 gap-2.5"
			onclick={() => (isOpen = !isOpen)}
		>
			<span class="relative flex h-2 w-2 shrink-0">
				{#if activeCluster}
				<span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
				<span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
				{:else}
				<span class="relative inline-flex rounded-full h-2 w-2 bg-surface-500"></span>
				{/if}
			</span>
			<span class="text-xs font-medium text-surface-200 max-w-32 truncate">
				{activeCluster?.name || 'No Cluster'}
			</span>
			<Icon name="chevron-down" size="sm" class="text-surface-500 transition-transform duration-200 {isOpen ? 'rotate-180' : ''}" />
		</Button>

		{#if isOpen}
			<div
				transition:fly={{ y: 5, duration: 200 }}
				class="absolute top-full right-0 mt-2 w-72 bg-[#1A1D21] border border-surface-700/50 rounded-xl shadow-2xl overflow-hidden z-50 ring-1 ring-black/5"
			>
				<!-- Header -->
				<div class="px-4 py-3 border-b border-surface-800/50 bg-surface-800/20">
					<span class="text-[10px] font-bold uppercase tracking-wider text-surface-400">
						Saved Clusters
					</span>
				</div>

				<!-- Cluster List -->
				<div class="max-h-64 overflow-y-auto py-1">
					{#each clusters as cluster}
						<button
							class="w-full text-left px-4 py-3 group hover:bg-surface-800/50 transition-colors relative flex items-start gap-3"
							onclick={() => handleSwitch(cluster)}
							disabled={switchingTo !== null}
						>
							<div class="mt-1.5">
								<div class="w-2 h-2 rounded-full ring-2 ring-offset-2 ring-offset-[#1A1D21] transition-all {cluster.is_active ? 'bg-emerald-500 ring-emerald-500/20' : 'bg-surface-600 ring-transparent group-hover:bg-surface-500'}"></div>
							</div>
							<div class="min-w-0 flex-1">
								<div class="flex items-center justify-between">
									<span class="text-sm font-medium text-surface-200 group-hover:text-white transition-colors">
										{cluster.name}
									</span>
									{#if switchingTo === cluster.id}
										<Icon name="spinner" size="sm" class="animate-spin text-primary" />
									{:else if cluster.is_active}
										<Icon name="check" size="sm" class="text-emerald-500" />
									{/if}
								</div>
								<p class="text-xs text-surface-500 font-mono mt-0.5 truncate group-hover:text-surface-400 transition-colors">
									{cluster.bootstrap_servers}
								</p>
							</div>
						</button>
					{/each}
				</div>

				<!-- Actions -->
				<div class="border-t border-surface-800/50 p-1 bg-surface-800/10 space-y-0.5">
					{#if activeCluster}
						<button
							class="w-full flex items-center gap-3 px-3 py-2 text-sm text-surface-400 hover:text-white hover:bg-surface-800/50 rounded-lg transition-colors group"
							onclick={handleDisconnect}
							disabled={loading}
						>
							{#if loading}
								<Icon name="spinner" size="sm" class="animate-spin" />
							{:else}
								<Icon name="x" size="sm" class="group-hover:text-red-400 transition-colors" />
							{/if}
							<span>Disconnect</span>
						</button>
					{/if}

					<a
						href="/settings"
						class="w-full flex items-center gap-3 px-3 py-2 text-sm text-surface-400 hover:text-white hover:bg-surface-800/50 rounded-lg transition-colors"
					>
						<Icon name="settings" size="sm" />
						<span>Manage Clusters</span>
					</a>
				</div>
			</div>
		{/if}
	</div>
{/if}

