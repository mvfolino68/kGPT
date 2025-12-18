<script lang="ts">
	interface Props {
		src: string;
		alt?: string;
		title?: string;
		width?: number | string;
		height?: number | string;
		loading?: 'lazy' | 'eager';
		class?: string;
	}

	let {
		src,
		alt = '',
		title,
		width,
		height,
		loading = 'lazy',
		class: className = ''
	}: Props = $props();

	let imageError = $state(false);
	let imageLoading = $state(true);

	function handleError() {
		imageError = true;
		imageLoading = false;
	}

	function handleLoad() {
		imageLoading = false;
	}
</script>

<div class="image-container {className}">
	{#if imageLoading && !imageError}
		<div class="image-placeholder">
			<svg
				class="w-8 h-8 text-surface-500 animate-pulse"
				fill="none"
				stroke="currentColor"
				viewBox="0 0 24 24"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
				/>
			</svg>
		</div>
	{/if}

	{#if imageError}
		<div class="image-error">
			<svg
				class="w-6 h-6 text-surface-600"
				fill="none"
				stroke="currentColor"
				viewBox="0 0 24 24"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
				/>
			</svg>
			<span class="text-xs text-surface-500 font-mono">Image failed to load</span>
		</div>
	{:else}
		<img
			src={src}
			alt={alt}
			title={title}
			width={width}
			height={height}
			loading={loading}
			onerror={handleError}
			onload={handleLoad}
			class="standardized-image {imageLoading ? 'opacity-0' : 'opacity-100'}"
		/>
	{/if}
</div>

<style>
	@reference "../../app.css";

	.image-container {
		@apply relative my-4 rounded-lg overflow-hidden border border-surface-700/50 bg-surface-900/30;
		@apply transition-all duration-200;
	}

	.image-container:hover {
		@apply border-surface-600/50 shadow-lg;
	}

	.image-placeholder {
		@apply absolute inset-0 flex items-center justify-center bg-surface-900/50;
		@apply min-h-[200px];
	}

	.image-error {
		@apply flex flex-col items-center justify-center gap-2 p-8 bg-surface-900/50;
		@apply min-h-[200px] text-center;
	}

	.standardized-image {
		@apply w-full h-auto max-w-full;
		@apply transition-opacity duration-200;
		@apply object-contain;
	}

	/* Ensure images don't overflow containers */
	.standardized-image {
		max-width: 100%;
		height: auto;
	}

	/* GIF-specific styling */
	.standardized-image[src$='.gif'],
	.standardized-image[src$='.GIF'] {
		@apply cursor-pointer;
	}

	/* Responsive sizing */
	@media (max-width: 768px) {
		.image-container {
			@apply my-3;
		}
	}
</style>
