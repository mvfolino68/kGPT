<script lang="ts">
	import { marked } from 'marked';
	import type { MarkedOptions } from 'marked';

	interface Props {
		content: string;
	}

	let { content }: Props = $props();

	// Create enhanced renderer with custom components
	function createRenderer() {
		const renderer = new marked.Renderer();

		// Marked v17 renderer signatures receive tokens, not strings.
		// Keep overrides minimal + stable; style the rest via CSS.
		renderer.code = function ({ text, lang }) {
			const language = lang || '';
			const escapedCode = text.replace(/</g, '&lt;').replace(/>/g, '&gt;');
			return `<div class="km-codeblock"><pre><code>${escapedCode}</code></pre>${language ? `<div class="km-code-lang">${language}</div>` : ''}</div>`;
		};

		renderer.link = function ({ href, title, tokens }) {
			const label = this.parser.parseInline(tokens);
			const safeTitle = title ? `title="${title.replace(/"/g, '&quot;')}"` : '';
			const safeHref = href?.replace(/"/g, '&quot;') ?? '';
			return `<a href="${safeHref}" ${safeTitle} class="km-link" target="_blank" rel="noopener noreferrer">${label}</a>`;
		};

		renderer.image = function ({ href, title, text }) {
			const alt = text || '';
			const safeHref = href?.replace(/"/g, '&quot;') ?? '';
			const safeAlt = alt.replace(/"/g, '&quot;');
			const titleAttr = title ? `title="${title.replace(/"/g, '&quot;')}"` : '';

			return `
				<div class="km-image">
					<img src="${safeHref}" alt="${safeAlt}" ${titleAttr} loading="lazy" />
					${alt ? `<div class="km-image-caption">${safeAlt}</div>` : ''}
				</div>
			`;
		};

		return renderer;
	}

	function renderMarkdown(content: string): string {
		try {
			// Clean up content
			let cleaned = content
				.replace(/^(Analysis|Answer|Response):\s*/gim, '')
				.replace(/\n{3,}/g, '\n\n')
				.trim();

			// Configure marked with custom renderer
			const renderer = createRenderer();
			const options: MarkedOptions = {
				breaks: true,
				gfm: true,
				renderer
			};

			return marked.parse(cleaned, options) as string;
		} catch (error) {
			console.error('Markdown rendering error:', error);
			return content.replace(/\n/g, '<br>');
		}
	}

	const htmlContent = $derived(renderMarkdown(content));
</script>

<div class="formatted-message prose prose-sm max-w-none prose-invert">
	{@html htmlContent}
</div>

<style>
	.formatted-message {
		-webkit-user-select: text;
		-moz-user-select: text;
		-ms-user-select: text;
		user-select: text;
	}

	.formatted-message :global(p) {
		color: rgb(var(--color-text));
		margin: 0.75rem 0;
		line-height: 1.65;
	}

	.formatted-message :global(a.km-link) {
		color: rgb(var(--color-primary));
		text-decoration: underline;
		text-underline-offset: 2px;
	}
	.formatted-message :global(a.km-link:hover) {
		color: rgb(var(--color-primary-hover));
	}

	.formatted-message :global(code:not(pre code)) {
		font-family: var(--font-family-mono);
		font-size: var(--font-size-sm);
		background: rgba(var(--color-surface), 0.55);
		padding: 0.1rem 0.35rem;
		border-radius: var(--radius-md);
		color: rgb(var(--color-primary));
	}

	.formatted-message :global(.km-codeblock) {
		position: relative;
		margin: 1rem 0;
	}
	.formatted-message :global(.km-codeblock pre) {
		background: rgb(var(--color-bg-elevated));
		border-radius: var(--radius-xl);
		padding: 1rem;
		overflow-x: auto;
	}
	.formatted-message :global(.km-codeblock code) {
		font-family: var(--font-family-mono);
		font-size: var(--font-size-sm);
		color: rgb(var(--color-text));
	}
	.formatted-message :global(.km-code-lang) {
		position: absolute;
		top: 0.5rem;
		right: 0.5rem;
		padding: 0.125rem 0.5rem;
		border-radius: var(--radius-md);
		background: rgba(var(--color-surface), 0.55);
		color: rgb(var(--color-text-tertiary));
		font-family: var(--font-family-mono);
		font-size: var(--font-size-2xs);
	}

	.formatted-message :global(blockquote) {
		border-left: 4px solid rgba(var(--color-border), 0.5);
		background: rgba(var(--color-bg-elevated), 0.55);
		border-radius: 0 var(--radius-lg) var(--radius-lg) 0;
		padding: 0.75rem 1rem;
		margin: 1rem 0;
		color: rgb(var(--color-text-secondary));
	}

	.formatted-message :global(ul),
	.formatted-message :global(ol) {
		margin: 1rem 0;
		padding-left: 1.25rem;
		color: rgb(var(--color-text));
	}

	.formatted-message :global(li) {
		margin: 0.25rem 0;
	}

	.formatted-message :global(::selection) {
		background: rgba(255, 235, 59, 0.65);
		color: inherit;
		text-shadow: none;
	}

	.formatted-message :global(::-moz-selection) {
		background: rgba(255, 235, 59, 0.65);
		color: inherit;
		text-shadow: none;
	}

	.formatted-message :global(.km-image) {
		margin: 1rem 0;
		border-radius: var(--radius-lg);
		overflow: hidden;
		background: rgba(var(--color-surface), 0.25);
	}
	.formatted-message :global(.km-image img) {
		display: block;
		width: 100%;
		height: auto;
		max-width: 100%;
		object-fit: contain;
	}
	.formatted-message :global(.km-image-caption) {
		padding: 0.5rem 0.75rem 0.75rem;
		text-align: center;
		font-family: var(--font-family-mono);
		font-size: var(--font-size-xs);
		color: rgb(var(--color-text-tertiary));
	}
</style>


