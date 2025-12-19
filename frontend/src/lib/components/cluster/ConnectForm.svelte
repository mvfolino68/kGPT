<script lang="ts">
	import { Button, Card } from '$lib/components/ui';
	import type { KafkaCluster } from '$lib/api';
	import SavedClusters from './SavedClusters.svelte';

	interface Props {
		showForm: boolean;
		formName: string;
		formBootstrap: string;
		formProtocol: string;
		connecting: boolean;
		clusters: KafkaCluster[];
		onShowForm: () => void;
		onHideForm: () => void;
		onSubmit: () => void;
		onConnect: (cluster: KafkaCluster) => void;
		onNameChange: (value: string) => void;
		onBootstrapChange: (value: string) => void;
		onProtocolChange: (value: string) => void;
	}

	let {
		showForm,
		formName,
		formBootstrap,
		formProtocol,
		connecting,
		clusters,
		onShowForm,
		onHideForm,
		onSubmit,
		onConnect,
		onNameChange,
		onBootstrapChange,
		onProtocolChange
	}: Props = $props();
</script>

<Card padding="none" variant="glass" class="bg-surface-900 ring-0 border border-surface-700/50">
	{#snippet header()}
		<div class="flex items-center justify-between">
			<div class="flex items-center gap-2">
				<span class="text-primary-light text-xs">+</span>
				<span class="text-[10px] font-bold text-surface-500 uppercase tracking-wider">Connect Cluster</span>
			</div>
			{#if !showForm}
				<Button variant="ghost" size="sm" onclick={onShowForm}>
					+ new
				</Button>
			{/if}
		</div>
	{/snippet}

	{#snippet children()}
		<div class="p-4">
			{#if showForm}
				<form onsubmit={(e) => { e.preventDefault(); onSubmit(); }} class="space-y-4">
					<div class="grid grid-cols-12 gap-3">
						<div class="col-span-3">
							<label for="cluster-connect-name" class="block text-[10px] font-bold text-surface-500 uppercase tracking-wider mb-1.5">Name</label>
							<input
								id="cluster-connect-name"
								type="text"
								value={formName}
								oninput={(e) => onNameChange(e.currentTarget.value)}
								placeholder="my-cluster"
								class="w-full bg-surface-700/50 border-none rounded-md px-3 py-2 text-sm text-foreground placeholder:text-muted transition-all focus:outline-none focus:bg-surface-700 focus:ring-2 focus:ring-primary-600/50"
							/>
						</div>
						<div class="col-span-5">
							<label for="cluster-connect-bootstrap" class="block text-[10px] font-bold text-surface-500 uppercase tracking-wider mb-1.5">Bootstrap</label>
							<input
								id="cluster-connect-bootstrap"
								type="text"
								value={formBootstrap}
								oninput={(e) => onBootstrapChange(e.currentTarget.value)}
								placeholder="localhost:9092"
								class="w-full bg-surface-700/50 border-none rounded-md px-3 py-2 text-sm text-foreground placeholder:text-muted transition-all focus:outline-none focus:bg-surface-700 focus:ring-2 focus:ring-primary-600/50"
							/>
						</div>
						<div class="col-span-4">
							<label for="cluster-connect-protocol" class="block text-[10px] font-bold text-surface-500 uppercase tracking-wider mb-1.5">Protocol</label>
							<select
								id="cluster-connect-protocol"
								value={formProtocol}
								onchange={(e) => onProtocolChange(e.currentTarget.value)}
								class="w-full bg-surface-700/50 border-none rounded-md px-3 py-2 text-sm text-foreground placeholder:text-muted transition-all focus:outline-none focus:bg-surface-700 focus:ring-2 focus:ring-primary-600/50"
							>
								<option value="PLAINTEXT">PLAINTEXT</option>
								<option value="SSL">SSL</option>
								<option value="SASL_PLAINTEXT">SASL_PLAINTEXT</option>
								<option value="SASL_SSL">SASL_SSL</option>
							</select>
						</div>
					</div>

					<div class="flex gap-2">
						<Button
							type="submit"
							variant="primary"
							disabled={connecting || !formName.trim() || !formBootstrap.trim()}
							loading={connecting}
						>
							Connect
						</Button>
						<Button type="button" variant="ghost" onclick={onHideForm}>
							Cancel
						</Button>
					</div>
				</form>
			{/if}

			{#if clusters.length > 0 && !showForm}
				<SavedClusters {clusters} {connecting} {onConnect} />
			{/if}
		</div>
	{/snippet}
</Card>
