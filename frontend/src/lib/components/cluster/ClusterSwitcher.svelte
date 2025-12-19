<script lang="ts">
	import { getClusters, connectCluster, disconnectCluster, type KafkaCluster } from '$lib/api';
	import { onMount } from 'svelte';

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
		<button
			type="button"
			class="flex items-center gap-2 text-xs hover:text-surface-200 transition-colors"
			onclick={() => (isOpen = !isOpen)}
		>
			<span class="text-surface-400 max-w-24 truncate">
				{activeCluster?.name || 'Select Cluster'}
			</span>
			<svg
				class="w-3 h-3 text-surface-500 transition-transform {isOpen ? 'rotate-180' : ''}"
				fill="none"
				stroke="currentColor"
				viewBox="0 0 24 24"
				stroke-width="2"
			>
				<path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
			</svg>
		</button>

		{#if isOpen}
			<div
				class="absolute top-full right-0 mt-2 w-64 bg-surface-800 border border-surface-700/30 rounded-lg shadow-2xl overflow-hidden z-50"
			>
				<div class="px-3 py-2">
					<span class="text-[10px] font-bold uppercase tracking-wider text-surface-400">
						Saved Clusters
					</span>
				</div>

				<div class="max-h-64 overflow-y-auto">
					{#each clusters as cluster}
						<button
							type="button"
							class="w-full text-left px-3 py-2.5 hover:bg-surface-600/50 transition-colors flex items-center justify-between gap-2 {cluster.is_active
								? 'bg-surface-600/40'
								: ''}"
							onclick={() => handleSwitch(cluster)}
							disabled={switchingTo !== null}
						>
							<div class="min-w-0 flex-1">
								<div class="flex items-center gap-2">
									<div
										class="w-2 h-2 rounded-full {cluster.is_active
											? 'bg-emerald-400'
											: 'bg-surface-500'}"
									></div>
									<span class="text-sm text-surface-200 truncate">{cluster.name}</span>
								</div>
								<p class="text-xs text-surface-400 font-mono truncate mt-0.5 ml-4">
									{cluster.bootstrap_servers}
								</p>
							</div>

							{#if switchingTo === cluster.id}
								<svg class="w-4 h-4 text-primary animate-spin shrink-0" fill="none" viewBox="0 0 24 24">
									<circle
										class="opacity-25"
										cx="12"
										cy="12"
										r="10"
										stroke="currentColor"
										stroke-width="4"
									></circle>
									<path
										class="opacity-75"
										fill="currentColor"
										d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
									></path>
								</svg>
							{:else if cluster.is_active}
								<svg class="w-4 h-4 text-emerald-400 shrink-0" fill="currentColor" viewBox="0 0 20 20">
									<path
										fill-rule="evenodd"
										d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
										clip-rule="evenodd"
									/>
								</svg>
							{/if}
						</button>
					{/each}
				</div>

				{#if activeCluster}
					<div class="pt-1">
						<button
							type="button"
							class="w-full text-left px-3 py-2.5 hover:bg-surface-600/50 transition-colors text-sm text-surface-300 flex items-center gap-2"
							onclick={handleDisconnect}
							disabled={loading}
						>
							{#if loading}
								<svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
									<circle
										class="opacity-25"
										cx="12"
										cy="12"
										r="10"
										stroke="currentColor"
										stroke-width="4"
									></circle>
									<path
										class="opacity-75"
										fill="currentColor"
										d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
									></path>
								</svg>
							{:else}
								<svg
									class="w-4 h-4"
									fill="none"
									stroke="currentColor"
									viewBox="0 0 24 24"
									stroke-width="1.5"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										d="M5.636 5.636a9 9 0 1012.728 0M12 3v9"
									/>
								</svg>
							{/if}
							Disconnect
						</button>
					</div>
				{/if}

				<div class="pb-1">
					<a
						href="/settings"
						class="block px-3 py-2.5 hover:bg-surface-600/50 transition-colors text-sm text-surface-300"
					>
						Manage Clusters
					</a>
				</div>
			</div>
		{/if}
	</div>
{/if}
