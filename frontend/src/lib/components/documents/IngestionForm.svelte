<script lang="ts">
	import { Panel } from '$lib/components/ui';
	import { type SourceType } from './types';
	import SourceTypeTabs from './SourceTypeTabs.svelte';
	import TextSourceInput from './TextSourceInput.svelte';
	import FileSourceInput from './FileSourceInput.svelte';
	import UrlSourceInput from './UrlSourceInput.svelte';
	import IngestionFooter from './IngestionFooter.svelte';

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
		onFileChange?: (file: File | null) => void;
		hasFile?: boolean;
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
		onFileChange,
		hasFile = false,
		onSmartNamingChange,
		onSelectSuggestion,
		onSubmit
	}: Props = $props();

	function handleFileSelect(file: File | null) {
		if (file) {
			if (!sourceName) {
				onSourceNameChange(file.name);
			}
			if (onFileChange) {
				onFileChange(file);
			}

			if (file.name.match(/\.(txt|md|json|csv)$/i)) {
				const reader = new FileReader();
				reader.onload = (e) => {
					if (e.target?.result) {
						onTextContentInput(e.target.result as string);
					}
				};
				reader.readAsText(file);
			} else {
				onTextContentInput('');
			}
		} else {
			if (onFileChange) onFileChange(null);
			onTextContentInput('');
		}
	}

	const isValidUrl = $derived(
		sourceType !== 'github' ? true : !sourceUrl || sourceUrl.startsWith('https://')
	);

	const urlError = $derived(
		!isValidUrl && sourceUrl.length > 0 ? 'URL must start with https://' : null
	);

	const canSubmit = $derived(
		!ingesting &&
		(sourceType === 'text' || sourceType === 'file'
			? (rawTextContent.trim().length > 0 || hasFile)
			: sourceUrl.trim().length > 0 && isValidUrl)
	);
</script>

<Panel padding="none" class="overflow-hidden">
	{#snippet children()}
		<div class="flex flex-col h-full">
			<SourceTypeTabs activeType={sourceType} onChange={onSourceTypeChange} />

			<div class="p-6">
				<form onsubmit={(e) => { e.preventDefault(); onSubmit(); }} class="space-y-6">
					{#if sourceType === 'text'}
						<TextSourceInput
							value={rawTextContent}
							onInput={onTextContentInput}
							loading={fetchingName}
						/>
					{:else if sourceType === 'file'}
						<FileSourceInput
							{hasFile}
							contentLength={rawTextContent.length}
							onFileSelect={handleFileSelect}
						/>
					{:else}
						<UrlSourceInput
							url={sourceUrl}
							onInput={onUrlInput}
							error={urlError}
							loading={fetchingName}
						/>
					{/if}

					<IngestionFooter
						name={sourceName}
						onNameChange={onSourceNameChange}
						{useSmartNaming}
						onSmartNamingChange={onSmartNamingChange}
						{smartName}
						suggestions={nameSuggestions}
						onSelectSuggestion={onSelectSuggestion}
						{ingesting}
						{canSubmit}
					/>
				</form>
			</div>
		</div>
	{/snippet}
</Panel>
