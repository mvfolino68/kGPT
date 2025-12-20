<script lang="ts">
	import { Icon, Input } from '$lib/components/ui';

	interface Props {
		url: string;
		onInput: (url: string) => void;
		error?: string | null;
		loading?: boolean;
	}

	let { url, onInput, error, loading = false }: Props = $props();
</script>

<div class="space-y-3 animate-in fade-in slide-in-from-bottom-2 duration-300">
	<label for="ingestion-source-url" class="text-xs font-semibold text-surface-300 uppercase tracking-wider flex items-center gap-2">
		Repository URL
	</label>
	<div class="relative">
		<div class="absolute left-3 top-1/2 -translate-y-1/2 text-surface-500">
			<Icon name="github" size="sm" />
		</div>
		<Input
			id="ingestion-source-url"
			type="text"
			value={url}
			oninput={(e) => onInput(e.currentTarget.value)}
			placeholder="https://github.com/username/repo"
			error={!!error}
			class="pl-10"
		/>
		{#if loading}
			<div class="absolute right-3 top-1/2 -translate-y-1/2">
				<Icon name="loader-2" class="animate-spin text-primary" size="sm" />
			</div>
		{/if}
	</div>
	{#if error}
		<div class="text-xs text-error flex items-center gap-1.5 pl-1">
			<Icon name="alert-circle" size="xs" />
			{error}
		</div>
	{/if}
	<p class="text-xs text-surface-500 pl-1">
		Supports public and private repositories.
	</p>
</div>
