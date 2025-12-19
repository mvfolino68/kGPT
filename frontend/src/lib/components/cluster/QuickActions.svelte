<script lang="ts">
	import { Button, Card, Icon } from '$lib/components/ui';

	interface Props {
		onAction: (action: string) => void;
		disabled?: boolean;
	}

	let { onAction, disabled = false }: Props = $props();

	const actions = [
		{ id: 'list_topics', label: 'List Topics', icon: 'folder' as const },
		{ id: 'describe_topic', label: 'Describe Topic', icon: 'info' as const },
		{ id: 'create_topic', label: 'Create Topic', icon: 'plus' as const },
		{ id: 'list_consumer_groups', label: 'Consumer Groups', icon: 'users' as const }
	];
</script>

<Card title="Quick Actions" padding="sm">
	{#snippet children()}
		<div class="flex items-center gap-2 flex-wrap">
			{#each actions as action}
				<Button
					variant="secondary"
					size="sm"
					{disabled}
					onclick={() => onAction(action.id)}
				>
					<Icon name={action.icon} size="sm" />
					{action.label}
				</Button>
			{/each}
		</div>
	{/snippet}
</Card>
