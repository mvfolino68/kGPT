<script lang="ts">
	import { Icon, Input, Button } from '$lib/components/ui';

	interface Props {
		name: string;
		onNameChange: (name: string) => void;
		useSmartNaming: boolean;
		onSmartNamingChange: (enabled: boolean) => void;
		smartName: string | null;
		suggestions: string[];
		onSelectSuggestion: (suggestion: string) => void;
		ingesting: boolean;
		canSubmit: boolean;
	}

	let {
		name,
		onNameChange,
		useSmartNaming,
		onSmartNamingChange,
		smartName,
		suggestions,
		onSelectSuggestion,
		ingesting,
		canSubmit
	}: Props = $props();
</script>

<div class="pt-6 border-t border-surface-700/30 flex flex-col md:flex-row gap-6 items-end">
	<div class="flex-1 space-y-3 w-full">
		<div class="flex items-center justify-between">
			<label for="ingestion-source-name" class="text-xs font-semibold text-surface-300 uppercase tracking-wider">
				Name
			</label>
			<label class="flex items-center gap-2 text-xs text-surface-400 cursor-pointer hover:text-surface-200 transition-colors">
				<input
					type="checkbox"
					checked={useSmartNaming}
					onchange={(e) => onSmartNamingChange(e.currentTarget.checked)}
					class="w-3.5 h-3.5 rounded bg-surface-700 border-surface-600 text-primary focus:ring-offset-surface-900"
				/>
				<span>AI Auto-naming</span>
			</label>
		</div>

		<div class="relative">
			<Input
				id="ingestion-source-name"
				type="text"
				value={name}
				oninput={(e) => onNameChange(e.currentTarget.value)}
				placeholder={smartName || 'Optional name...'}
			/>
		</div>

		{#if suggestions.length > 0 && !name}
			<div class="flex flex-wrap gap-2 animate-in fade-in slide-in-from-top-1">
				{#each suggestions as suggestion}
					<button
						type="button"
						class="text-xs px-2.5 py-1 rounded-md bg-surface-800 hover:bg-surface-700 text-surface-300 border border-surface-700 hover:border-surface-600 transition-all"
						onclick={() => onSelectSuggestion(suggestion)}
					>
						{suggestion}
					</button>
				{/each}
			</div>
		{/if}
	</div>

	<Button
		type="submit"
		variant="primary"
		class="w-full md:w-auto min-w-[140px]"
		disabled={!canSubmit || ingesting}
	>
		{ingesting ? 'Ingesting...' : 'Add Source'}
		{#if !ingesting}
			<Icon name="plus" size="sm" class="ml-2" />
		{/if}
	</Button>
</div>
