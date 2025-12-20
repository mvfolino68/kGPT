<script lang="ts">
	import { Button, Icon } from '$lib/components/ui';

	interface Props {
		onAction: (message: string) => void;
	}

	let { onAction }: Props = $props();

	const suggestions = [
		{ label: 'List all topics', value: 'List all topics' },
		{ label: 'Show consumer groups', value: 'Show consumer groups' },
		{ label: 'How do I create a topic?', value: 'How do I create a topic?' }
	];
</script>

<div class="flex flex-col items-center justify-center h-full text-center py-8">
	<div class="w-14 h-14 rounded-2xl bg-primary/10 flex items-center justify-center mb-4">
		<Icon name="sparkles" size="lg" class="text-primary-light" />
	</div>
	<h3 class="text-lg font-semibold text-surface-200 mb-2">How can I help?</h3>
	<p class="text-sm text-surface-500 max-w-xs mb-6">
		Ask me to manage topics, describe consumer groups, or help with Kafka configuration.
	</p>

	<div class="space-y-2 w-full max-w-xs">
		{#each suggestions as suggestion}
			<Button
				variant="secondary"
				size="sm"
				class="w-full justify-start text-left text-surface-300"
				onclick={() => onAction(suggestion.value)}
			>
				{suggestion.label}
			</Button>
		{/each}
	</div>
</div>
