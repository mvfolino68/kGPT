<script lang="ts">
	import { Button, Panel, Card, Icon, Input, Textarea } from '$lib/components/ui';
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

	// File Handling
	let fileInputFn: HTMLInputElement;
	let dragOver = $state(false);

	function handleFileSelect(e: Event) {
		const target = e.target as HTMLInputElement;
		if (target.files && target.files.length > 0) {
			readFile(target.files[0]);
		}
	}

	function handleDrop(e: DragEvent) {
		e.preventDefault();
		dragOver = false;
		if (e.dataTransfer && e.dataTransfer.files.length > 0) {
			readFile(e.dataTransfer.files[0]);
		}
	}

	function readFile(file: File) {
		// Auto-set name if empty
		if (!sourceName) {
			onSourceNameChange(file.name);
		}

		if (onFileChange) {
			onFileChange(file);
		}

		// Only read text content for text files
		if (file.name.match(/\.(txt|md|json|csv)$/i)) {
			const reader = new FileReader();
			reader.onload = (e) => {
				if (e.target?.result) {
					const content = e.target.result as string;
					onTextContentInput(content);
				}
			};
			reader.readAsText(file);
		} else {
			// For binaries like PDF, we just signal the file is ready (via onFileChange => hasFile)
			// Clear text content as we won't send it as raw text
			onTextContentInput('');
		}
	}

	// Validation
	const isValidUrl = $derived(
		sourceType !== 'github' // Only validate URL for github (and other url-based types if added)
			? true
			: !sourceUrl || sourceUrl.startsWith('https://')
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

	const getIconForType = (type: SourceType) => {
		switch (type) {
			case 'github': return 'github';
			case 'file': return 'file-text';
			case 'text': return 'align-left';
			default: return 'link';
		}
	};
</script>

<Panel padding="none" class="overflow-hidden">
	{#snippet children()}
		<div class="flex flex-col h-full">
			<!-- Integrated Header & Tabs -->
			<div class="border-b border-white/5 p-1">
				<div class="grid grid-cols-3 gap-1">
					{#each sourceTypeOptions as option}
						{@const isSelected = sourceType === option.value}
						<button
							class="flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all duration-200
								{isSelected
									? 'bg-surface-700 text-white shadow-sm ring-1 ring-white/10'
									: 'text-surface-400 hover:text-surface-200 hover:bg-surface-800'}"
							onclick={() => onSourceTypeChange(option.value)}
						>
							<Icon name={getIconForType(option.value)} size="sm" />
							{option.label}
						</button>
					{/each}
				</div>
			</div>

			<!-- Main Content Area -->
			<div class="p-6">
				<form onsubmit={(e) => { e.preventDefault(); onSubmit(); }} class="space-y-6">

					{#if sourceType === 'text'}
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
									value={rawTextContent}
									oninput={(e) => onTextContentInput((e.target as HTMLTextAreaElement).value)}
									placeholder="Paste your content here..."
									rows={10}
								/>
								{#if fetchingName}
									<div class="absolute right-4 bottom-4">
										<Icon name="loader-2" class="animate-spin text-primary" size="sm" />
									</div>
								{/if}
							</div>
						</div>

					{:else if sourceType === 'file'}
						<div class="space-y-3 animate-in fade-in slide-in-from-bottom-2 duration-300">
							<div class="flex items-center justify-between">
								<label for="ingestion-file-upload" class="text-xs font-semibold text-surface-300 uppercase tracking-wider">
									Upload File
								</label>
								<span class="text-xs text-surface-500">.pdf, .txt, .md, .json, .csv</span>
							</div>

							<input
								bind:this={fileInputFn}
								type="file"
								id="ingestion-file-upload"
								class="hidden"
								accept=".pdf,.txt,.md,.json,.csv"
								onchange={handleFileSelect}
							/>

							<!-- Drop Zone -->
							<button
								type="button"
								class="w-full h-48 rounded-xl border-2 border-dashed transition-all duration-200 flex flex-col items-center justify-center gap-3
									{dragOver ? 'border-primary bg-primary/5' : 'border-surface-700/50 bg-surface-900/20 hover:border-primary/30 hover:bg-surface-900/40'}
									{rawTextContent || hasFile ? 'border-success/50 bg-success/5' : ''}"
								ondragover={(e) => { e.preventDefault(); dragOver = true; }}
								ondragleave={() => dragOver = false}
								ondrop={handleDrop}
								onclick={() => fileInputFn?.click()}
							>
								{#if rawTextContent || hasFile}
									<div class="w-12 h-12 rounded-full bg-success/20 flex items-center justify-center text-success mb-1">
										<Icon name="check" size="md" />
									</div>
									<div class="text-center">
										<p class="text-sm font-medium text-foreground">File Loaded</p>
										<p class="text-xs text-surface-400 mt-1">
											{hasFile ? 'Ready to ingest' : `${Math.round(rawTextContent.length / 1024 * 10) / 10} KB loaded`}
										</p>
									</div>
									<Button variant="ghost" size="xs" class="mt-2 text-surface-400 hover:text-error" onclick={(e) => { e.stopPropagation(); onTextContentInput(''); if(onFileChange) onFileChange(null); }}>
										Remove
									</Button>
								{:else}
									<div class="w-12 h-12 rounded-full bg-surface-800 flex items-center justify-center text-surface-400 mb-1 group-hover:scale-110 transition-transform">
										<Icon name="upload-cloud" size="md" />
									</div>
									<div class="text-center">
										<p class="text-sm font-medium text-surface-200">Click to upload or drag and drop</p>
										<p class="text-xs text-surface-500 mt-1">Maximum size 5MB</p>
									</div>
								{/if}
							</button>
						</div>

					{:else}
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
									value={sourceUrl}
									oninput={(e) => onUrlInput((e.target as HTMLInputElement).value)}
									placeholder="https://github.com/username/repo"
									error={!!urlError}
									class="pl-10"
								/>
								{#if fetchingName}
									<div class="absolute right-3 top-1/2 -translate-y-1/2">
										<Icon name="loader-2" class="animate-spin text-primary" size="sm" />
									</div>
								{/if}
							</div>
							{#if urlError}
								<div class="text-xs text-error flex items-center gap-1.5 pl-1">
									<Icon name="alert-circle" size="xs" />
									{urlError}
								</div>
							{/if}
							<p class="text-xs text-surface-500 pl-1">
								Supports public and private repositories.
							</p>
						</div>
					{/if}

					<!-- Footer Actions -->
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
									value={sourceName}
									oninput={(e) => onSourceNameChange((e.target as HTMLInputElement).value)}
									placeholder={smartName || 'Optional name...'}
								/>
							</div>

							{#if nameSuggestions.length > 0 && !sourceName}
								<div class="flex flex-wrap gap-2 animate-in fade-in slide-in-from-top-1">
									{#each nameSuggestions as suggestion}
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
						>
							{ingesting ? 'Ingesting...' : 'Add Source'}
							{#if !ingesting}
								<Icon name="plus" size="sm" class="ml-2" />
							{/if}
						</Button>
					</div>
				</form>
			</div>
		</div>
	{/snippet}
</Panel>
