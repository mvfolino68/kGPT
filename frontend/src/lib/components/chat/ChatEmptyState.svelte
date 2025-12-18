<script lang="ts">
	import { RetroButton, RetroCard } from '$lib/components';

	interface Props {
		onQuickAction: (value: string) => void;
	}

	let { onQuickAction }: Props = $props();

	const quickActions = [
		{ label: 'Cluster status', value: 'Show me my Kafka cluster status' },
		{ label: 'List topics', value: 'List all topics in my cluster' },
		{ label: 'Consumer lag', value: 'Show consumer group lag' },
		{ label: 'What can you do?', value: 'What admin operations can you perform?' }
	];
</script>

<RetroCard variant="glow-blue" class="text-center py-12">
	<div class="w-20 h-20 rounded-xl retro-card-glow-blue flex items-center justify-center mb-6 animate-glow-pulse mx-auto">
		<svg class="w-10 h-10 text-confluent-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
			<path stroke-linecap="round" stroke-linejoin="round" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
		</svg>
	</div>
	<h2 class="text-2xl font-bold font-mono text-surface-100 mb-2 text-glow-blue">READY_</h2>
	<p class="text-surface-400 mb-8 max-w-md font-mono text-sm mx-auto">Query Kafka cluster, search docs, perform admin ops</p>

	<div class="flex flex-wrap justify-center gap-2">
		{#each quickActions as action}
			<RetroButton size="sm" onclick={() => onQuickAction(action.value)}>
				{action.label}
			</RetroButton>
		{/each}
	</div>
</RetroCard>
