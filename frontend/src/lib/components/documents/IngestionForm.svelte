<script lang="ts">
	import { Button, Panel } from '$lib/components/ui';
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

<Panel title="Add Internal Docs">
	{#snippet children()}
	<div class="space-y-4">
		<!-- Source type selection -->
		<div class="flex gap-2">
			{#each sourceTypeOptions as option}
				{@const isSelected = sourceType === option.value}
				<Button
					variant={isSelected ? 'secondary' : 'ghost'}
					size="lg"
					class="flex-1 justify-start text-left h-auto p-4 rounded-xl border {isSelected ? 'bg-surface-800 border-primary/20 ring-1 ring-primary/20' : 'border-transparent bg-surface-800/30'}"
					onclick={() => onSourceTypeChange(option.value)}
				>
					<div class="w-full">
						<div class="text-sm font-semibold {isSelected ? 'text-primary' : 'text-surface-300'}">
							{option.label}
						</div>
						<div class="text-xs text-surface-500 mt-1 font-normal leading-relaxed">{option.description}</div>
					</div>
				</Button>
			{/each}
		</div>

		<form onsubmit={(e) => { e.preventDefault(); onSubmit(); }} class="space-y-4">
			{#if sourceType === 'text'}
				<div>
					<label for="ingestion-raw-text" class="block text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-1.5">
						Raw Text Content
					</label>
					<div class="relative">
						<textarea
							id="ingestion-raw-text"
							value={rawTextContent}
							oninput={(e) => onTextContentInput(e.currentTarget.value)}
							placeholder="Paste your raw text content here..."
							rows="10"
							class="w-full bg-surface-700/50 border-none rounded-md px-3 py-2 text-sm text-foreground placeholder:text-muted transition-all focus:outline-none focus:bg-surface-700 focus:ring-2 focus:ring-primary-600/50"
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
					<label for="ingestion-source-url" class="block text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-1.5">
						{sourceType === 'github' ? 'Repository URL' : 'File Path'}
					</label>
					<div class="relative">
						<input
							id="ingestion-source-url"
							type="text"
							value={sourceUrl}
							oninput={(e) => onUrlInput(e.currentTarget.value)}
							placeholder={sourceType === 'github' ? 'https://github.com/org/repo' : '/path/to/file.pdf or file name'}
							class="w-full bg-surface-700/50 border-none rounded-md px-3 py-2 pr-10 text-sm text-foreground placeholder:text-muted transition-all focus:outline-none focus:bg-surface-700 focus:ring-2 focus:ring-primary-600/50"
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
					<label for="ingestion-source-name" class="text-[10px] font-bold uppercase tracking-wider text-surface-500">Name</label>
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
					id="ingestion-source-name"
					type="text"
					value={sourceName}
					oninput={(e) => onSourceNameChange(e.currentTarget.value)}
					placeholder={smartName || 'auto-generated'}
					class="w-full input"
				/>

				{#if nameSuggestions.length > 0 && !sourceName}
					<div class="flex flex-wrap gap-1.5 mt-2">
						{#each nameSuggestions as suggestion}
							<Button
								variant="ghost"
								size="xs"
								onclick={() => onSelectSuggestion(suggestion)}
							>
								{suggestion}
							</Button>
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
				<Button
					type="submit"
					variant="primary"
					disabled={!canSubmit}
					loading={ingesting}
				>
					Add to Knowledge Base
				</Button>
			</div>
		</form>
	</div>
	{/snippet}
</Panel>
