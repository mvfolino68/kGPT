<script lang="ts">
	interface Props {
		actions: Array<{ label: string; value: string }>;
		onActionClick: (value: string) => void;
	}

	let { actions, onActionClick }: Props = $props();
</script>

{#if actions.length > 0}
	<div class="flex flex-wrap gap-2 pt-1">
		{#each actions as action}
			<button
				type="button"
				onclick={() => onActionClick(action.value)}
				class="btn btn-ghost btn-sm"
			>
				{action.label}
			</button>
		{/each}
	</div>
{/if}
