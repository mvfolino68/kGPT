<script lang="ts">
	import { Button, Card } from '$lib/components/ui';

	interface Props {
		onConnectDemo: () => void;
	}

	let { onConnectDemo }: Props = $props();
</script>

<Card padding="none" variant="glass" class="bg-surface-900 ring-0 border border-surface-700/50">
	{#snippet header()}
		<div class="flex items-center gap-2">
			<svg class="w-4 h-4 text-primary-light" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
				<path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
			</svg>
			<span class="text-[10px] font-bold text-surface-500 uppercase tracking-wider">Quick Connect</span>
		</div>
	{/snippet}
	{#snippet children()}
		<div class="p-4 space-y-3">
			<Button variant="default" class="w-full" onclick={onConnectDemo}>
				Demo Cluster <span class="text-muted ml-1">(docker)</span>
			</Button>
			<p class="text-xs text-surface-600">
				Running: docker compose --profile demo up?
			</p>
		</div>
	{/snippet}
</Card>
