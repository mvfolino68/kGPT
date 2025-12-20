<script lang="ts">
	import { Icon, Button } from '$lib/components/ui';

	interface Props {
		hasFile: boolean;
		contentLength: number;
		onFileSelect: (file: File | null) => void;
	}

	let { hasFile, contentLength, onFileSelect }: Props = $props();

	let fileInputFn: HTMLInputElement;
	let dragOver = $state(false);

	function handleFileSelect(e: Event) {
		const target = e.target as HTMLInputElement;
		if (target.files && target.files.length > 0) {
			onFileSelect(target.files[0]);
		}
	}

	function handleDrop(e: DragEvent) {
		e.preventDefault();
		dragOver = false;
		if (e.dataTransfer && e.dataTransfer.files.length > 0) {
			onFileSelect(e.dataTransfer.files[0]);
		}
	}
</script>

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

	<button
		type="button"
		class="w-full h-48 rounded-xl border-2 border-dashed transition-all duration-200 flex flex-col items-center justify-center gap-3
			{dragOver ? 'border-primary bg-primary/5' : 'border-surface-700/50 bg-surface-900/20 hover:border-primary/30 hover:bg-surface-900/40'}
			{contentLength > 0 || hasFile ? 'border-success/50 bg-success/5' : ''}"
		ondragover={(e) => { e.preventDefault(); dragOver = true; }}
		ondragleave={() => dragOver = false}
		ondrop={handleDrop}
		onclick={() => fileInputFn?.click()}
	>
		{#if contentLength > 0 || hasFile}
			<div class="w-12 h-12 rounded-full bg-success/20 flex items-center justify-center text-success mb-1">
				<Icon name="check" size="md" />
			</div>
			<div class="text-center">
				<p class="text-sm font-medium text-foreground">File Loaded</p>
				<p class="text-xs text-surface-400 mt-1">
					{hasFile ? 'Ready to ingest' : `${Math.round(contentLength / 1024 * 10) / 10} KB loaded`}
				</p>
			</div>
			<Button variant="ghost" size="xs" class="mt-2 text-surface-400 hover:text-error" onclick={(e) => { e.stopPropagation(); onFileSelect(null); }}>
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
