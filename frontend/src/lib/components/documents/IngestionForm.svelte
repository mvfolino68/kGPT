<script lang="ts">
	import { sourceTypeOptions, type SourceType } from './types';

	interface Props {
		sourceType: SourceType;
		sourceName: string;
		sourceUrl: string;
		rawTextContent: string;
		useSmartNaming: boolean;
		nameSuggestions: string[];
		smartName: string | null;
		fetchingName: boolean;
		ingesting: boolean;
		onSourceTypeChange: (type: SourceType) => void;
		onSourceNameChange: (name: string) => void;
		onUrlInput: (url: string) => void;
		onTextContentInput: (content: string) => void;
		onSmartNamingChange: (enabled: boolean) => void;
		onSelectSuggestion: (name: string) => void;
		onSubmit: () => void;
	}

	let {
		sourceType,
		sourceName,
		sourceUrl,
		rawTextContent,
		useSmartNaming,
		nameSuggestions,
		smartName,
		fetchingName,
		ingesting,
		onSourceTypeChange,
		onSourceNameChange,
		onUrlInput,
		onTextContentInput,
		onSmartNamingChange,
		onSelectSuggestion,
		onSubmit
	}: Props = $props();

	const canSubmit = $derived(
		!ingesting && (sourceType === 'text' ? rawTextContent.trim() : sourceUrl.trim())
	);
</script>

<div class="panel overflow-hidden">
	<div class="panel-header flex items-center justify-between">
		<div class="flex items-center gap-2">
			<span class="text-surface-400 text-xs">+</span>
			<span class="text-sm text-surface-300">Add Internal Docs</span>
		</div>
	</div>

	<div class="p-4 space-y-4">
		<!-- Source type selection -->
		<div class="flex gap-2">
			{#each sourceTypeOptions as option}
				<button
					type="button"
					onclick={() => onSourceTypeChange(option.value)}
					class="flex-1 p-3 rounded-lg border transition-all text-left {sourceType === option.value
						? 'border-surface-600/50 bg-surface-800/60'
						: 'border-surface-700/30 bg-surface-800/30 hover:border-surface-600/40'}"
				>
					<div class="text-sm {sourceType === option.value ? 'text-surface-100' : 'text-surface-300'}">
						{option.label}
					</div>
					<div class="text-xs text-surface-500 mt-0.5">{option.description}</div>
				</button>
			{/each}
		</div>

		<form onsubmit={(e) => { e.preventDefault(); onSubmit(); }} class="space-y-4">
			{#if sourceType === 'text'}
				<div>
					<label class="block text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-1.5">
						Raw Text Content
					</label>
					<div class="relative">
						<textarea
							value={rawTextContent}
							oninput={(e) => onTextContentInput(e.currentTarget.value)}
							placeholder="Paste your raw text content here..."
							rows="10"
							class="w-full input text-sm"
						></textarea>
						{#if fetchingName}
							<div class="absolute right-3 top-3">
								<svg class="w-4 h-4 animate-spin text-surface-500" fill="none" viewBox="0 0 24 24">
									<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
									<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
								</svg>
							</div>
						{/if}
					</div>
				</div>
			{:else}
				<div>
					<label class="block text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-1.5">
						{sourceType === 'github' ? 'Repository URL' : 'File Path'}
					</label>
					<div class="relative">
						<input
							type="text"
							value={sourceUrl}
							oninput={(e) => onUrlInput(e.currentTarget.value)}
							placeholder={sourceType === 'github' ? 'https://github.com/org/repo' : '/path/to/file.pdf or file name'}
							class="w-full input pr-10"
						/>
						{#if fetchingName}
							<div class="absolute right-3 top-1/2 -translate-y-1/2">
								<svg class="w-4 h-4 animate-spin text-surface-500" fill="none" viewBox="0 0 24 24">
									<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
									<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
								</svg>
							</div>
						{/if}
					</div>
				</div>
			{/if}

			<div>
				<div class="flex items-center justify-between mb-1.5">
					<label class="text-[10px] font-bold uppercase tracking-wider text-surface-500">Name</label>
					<label class="flex items-center gap-1.5 text-xs text-surface-500 cursor-pointer">
						<input
							type="checkbox"
							checked={useSmartNaming}
							onchange={(e) => onSmartNamingChange(e.currentTarget.checked)}
							class="w-3 h-3 rounded bg-surface-700 border-surface-600"
						/>
						<span>AI naming</span>
					</label>
				</div>
				<input
					type="text"
					value={sourceName}
					oninput={(e) => onSourceNameChange(e.currentTarget.value)}
					placeholder={smartName || 'auto-generated'}
					class="w-full input"
				/>

				{#if nameSuggestions.length > 0 && !sourceName}
					<div class="flex flex-wrap gap-1.5 mt-2">
						{#each nameSuggestions as suggestion}
							<button
								type="button"
								onclick={() => onSelectSuggestion(suggestion)}
								class="px-2 py-1 text-xs bg-surface-800/50 hover:bg-surface-700/50 text-surface-300 rounded border border-surface-700/30 hover:border-surface-600/40 transition-colors"
							>
								{suggestion}
							</button>
						{/each}
					</div>
				{/if}
			</div>

			<div class="flex items-center justify-between pt-2">
				<div class="text-xs text-surface-500">
					{#if smartName && useSmartNaming && !sourceName}
						Will use: <span class="text-primary-light">{smartName}</span>
					{:else if sourceName}
						Using: <span class="text-surface-300">{sourceName}</span>
					{:else}
						Name will be auto-generated
					{/if}
				</div>
				<button
					type="submit"
					disabled={!canSubmit}
					class="btn btn-primary"
				>
					{ingesting ? 'Indexing...' : 'Add to Knowledge Base'}
				</button>
			</div>
		</form>
	</div>
</div>
