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
	.image-container {
		position: relative;
		margin: 1rem 0;
		border-radius: var(--radius-lg);
		overflow: hidden;
		border: 1px solid rgba(var(--color-border), 0.5);
		background: rgba(var(--color-bg-elevated), 0.35);
		transition: border-color 150ms ease, box-shadow 150ms ease;
	}

	.image-container:hover {
		border-color: rgba(var(--color-border), 0.7);
		box-shadow: 0 10px 30px rgba(0, 0, 0, 0.45);
	}

	.image-placeholder {
		position: absolute;
		inset: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		background: rgba(var(--color-bg-elevated), 0.55);
		min-height: 200px;
	}

	.image-error {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		padding: 2rem;
		background: rgba(var(--color-bg-elevated), 0.55);
		min-height: 200px;
		text-align: center;
	}

	.standardized-image {
		width: 100%;
		height: auto;
		max-width: 100%;
		object-fit: contain;
		transition: opacity 200ms ease;
	}

	/* Ensure images don't overflow containers */
	.standardized-image {
		max-width: 100%;
		height: auto;
	}

	/* GIF-specific styling */
	.standardized-image[src$='.gif'],
	.standardized-image[src$='.GIF'] {
		cursor: pointer;
	}

	/* Responsive sizing */
	@media (max-width: 768px) {
		.image-container {
			margin: 0.75rem 0;
		}
	}
</style>
