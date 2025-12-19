<script lang="ts">
	import { Button } from '$lib/components/ui';
	import { EmptyState } from '$lib/components/common';

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

<EmptyState
	title="Ready"
	description="Query your Kafka cluster, search documentation, or perform admin operations"
	class="bg-surface-800 rounded-lg"
>
	{#snippet iconSnippet()}
		<div class="w-20 h-20 rounded-xl bg-surface-700/50 flex items-center justify-center mb-6 mx-auto">
			<svg class="w-10 h-10 text-primary-light" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
				<path stroke-linecap="round" stroke-linejoin="round" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
			</svg>
		</div>
	{/snippet}

	<div class="flex flex-wrap justify-center gap-2 mt-6">
		{#each quickActions as action}
			<Button variant="ghost" size="sm" onclick={() => onQuickAction(action.value)}>
				{action.label}
			</Button>
		{/each}
	</div>
</EmptyState>
