<script lang="ts">
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

<div class="bg-surface-900 border border-surface-700/50 rounded-lg overflow-hidden">
	<div class="flex items-center justify-between px-4 py-3 border-b border-surface-700/50">
		<div class="flex items-center gap-2">
			<span class="text-primary-light text-xs">+</span>
			<span class="text-[10px] font-bold text-surface-500 uppercase tracking-wider">Connect Cluster</span>
		</div>
		{#if !showForm}
			<button type="button" class="btn btn-ghost btn-sm" onclick={onShowForm}>
				+ new
			</button>
		{/if}
	</div>

	<div class="p-4">
		{#if showForm}
			<form onsubmit={(e) => { e.preventDefault(); onSubmit(); }} class="space-y-4">
				<div class="grid grid-cols-12 gap-3">
					<div class="col-span-3">
						<label class="block text-[10px] font-bold text-surface-500 uppercase tracking-wider mb-1.5">Name</label>
						<input
							type="text"
							value={formName}
							oninput={(e) => onNameChange(e.currentTarget.value)}
							placeholder="my-cluster"
							class="w-full input"
						/>
					</div>
					<div class="col-span-5">
						<label class="block text-[10px] font-bold text-surface-500 uppercase tracking-wider mb-1.5">Bootstrap</label>
						<input
							type="text"
							value={formBootstrap}
							oninput={(e) => onBootstrapChange(e.currentTarget.value)}
							placeholder="localhost:9092"
							class="w-full input"
						/>
					</div>
					<div class="col-span-4">
						<label class="block text-[10px] font-bold text-surface-500 uppercase tracking-wider mb-1.5">Protocol</label>
						<select
							value={formProtocol}
							onchange={(e) => onProtocolChange(e.currentTarget.value)}
							class="w-full input"
						>
							<option value="PLAINTEXT">PLAINTEXT</option>
							<option value="SSL">SSL</option>
							<option value="SASL_PLAINTEXT">SASL_PLAINTEXT</option>
							<option value="SASL_SSL">SASL_SSL</option>
						</select>
					</div>
				</div>

				<div class="flex gap-2">
					<button
						type="submit"
						class="btn btn-primary"
						disabled={connecting || !formName.trim() || !formBootstrap.trim()}
					>
						{connecting ? 'Connecting...' : 'Connect'}
					</button>
					<button type="button" class="btn btn-ghost" onclick={onHideForm}>
						Cancel
					</button>
				</div>
			</form>
		{/if}

		{#if clusters.length > 0 && !showForm}
			<SavedClusters {clusters} {connecting} {onConnect} />
		{/if}
	</div>
</div>
