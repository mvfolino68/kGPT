<script lang="ts">
	import { Modal, LoadingSpinner, Input, Icon } from '$lib/components/ui';
	import { getBrokerConfig } from '$lib/api';

	interface Props {
		brokerId: number | null;
		onClose: () => void;
	}

	let { brokerId, onClose }: Props = $props();

	let fullConfig = $state<any>(null);
	let loading = $state(false);
	let error = $state<string | null>(null);
	let searchTerm = $state('');

	$effect(() => {
		if (brokerId !== null) {
			loadConfig(brokerId);
		} else {
			fullConfig = null;
			error = null;
			searchTerm = '';
		}
	});

	async function loadConfig(id: number) {
		loading = true;
		error = null;
		try {
			fullConfig = await getBrokerConfig(id);
		} catch (e: any) {
			error = e.message || 'Failed to load broker configuration';
		} finally {
			loading = false;
		}
	}

	// Transform config object into a sorted array of [key, value] pairs
	let configItems = $derived.by(() => {
		if (!fullConfig?.config) return [];

		const entries = Object.entries(fullConfig.config)
			.map(([key, value]) => ({ key, value }))
			.sort((a, b) => a.key.localeCompare(b.key));

		if (!searchTerm) return entries;

		const lowerSearch = searchTerm.toLowerCase();
		return entries.filter(item =>
			item.key.toLowerCase().includes(lowerSearch) ||
			String(item.value).toLowerCase().includes(lowerSearch)
		);
	});
</script>

<Modal
	isOpen={brokerId !== null}
	title={`Broker ${brokerId} Configuration`}
	size="xl"
	onClose={onClose}
>
	{#if loading}
		<div class="flex items-center justify-center py-12">
			<LoadingSpinner size="lg" />
		</div>
	{:else if error}
		<div class="p-4 rounded-lg bg-error-bg text-error text-sm">
			{error}
		</div>
	{:else if fullConfig}
		<div class="space-y-4">
			<!-- Search bar -->
			<div class="sticky top-0 z-10 bg-surface-900 pb-2">
				<Input
					type="text"
					placeholder="Search configuration keys..."
					bind:value={searchTerm}
				>
					{#snippet prefix()}
						<Icon name="search" size="sm" class="text-text-tertiary" />
					{/snippet}
				</Input>
			</div>

			<!-- Config List -->
			<div class="border border-border-subtle rounded-lg overflow-hidden">
				{#if configItems.length === 0}
					<div class="p-8 text-center text-text-tertiary text-sm">
						No configuration found matching "{searchTerm}"
					</div>
				{:else}
					<div class="divide-y divide-border-subtle">
						{#each configItems as item (item.key)}
							<div class="p-3 hover:bg-surface-hover flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 group transition-colors">
								<div class="min-w-0 flex-1">
									<div class="text-sm font-mono text-primary-light break-all" title={item.key}>
										{item.key}
									</div>
								</div>
								<div class="font-mono text-sm text-text-secondary break-all sm:text-right sm:max-w-[50%]">
									{#if item.value === null}
										<span class="text-text-tertiary italic">null</span>
									{:else if item.value === ''}
										<span class="text-text-tertiary italic">empty string</span>
									{:else}
										{item.value}
									{/if}
								</div>
							</div>
						{/each}
					</div>
				{/if}
			</div>

			<div class="text-xs text-text-tertiary text-right pt-2">
				Showing {configItems.length} of {Object.keys(fullConfig.config || {}).length} configurations
			</div>
		</div>
	{/if}
</Modal>
