<script lang="ts">
	import { Icon, Textarea } from '$lib/components/ui';

	interface Props {
		value: string;
		onInput: (value: string) => void;
		loading?: boolean;
	}

	let { value, onInput, loading = false }: Props = $props();
</script>

<div class="space-y-3 animate-in fade-in slide-in-from-bottom-2 duration-300">
	<div class="flex items-center justify-between">
		<label for="ingestion-raw-text" class="text-xs font-semibold text-surface-300 uppercase tracking-wider">
			Raw Text Content
		</label>
		<span class="text-xs text-surface-500">Paste snippet or memo</span>
	</div>
	<div class="relative group">
		<Textarea
			id="ingestion-raw-text"
			{value}
			oninput={(e) => onInput(e.currentTarget.value)}
			placeholder="Paste your content here..."
			rows={10}
		/>
		{#if loading}
			<div class="absolute right-4 bottom-4">
				<Icon name="loader-2" class="animate-spin text-primary" size="sm" />
			</div>
		{/if}
	</div>
</div>
