<script lang="ts">
	import { Button } from '$lib/components/ui';

	interface Props {
		actions: Array<{ label: string; value: string }>;
		onActionClick: (value: string) => void;
	}

	let { actions, onActionClick }: Props = $props();
</script>

{#if actions.length > 0}
	<div class="flex flex-wrap gap-2 pt-1">
		{#each actions as action}
			<Button variant="ghost" size="sm" onclick={() => onActionClick(action.value)}>
				{action.label}
			</Button>
		{/each}
	</div>
{/if}

