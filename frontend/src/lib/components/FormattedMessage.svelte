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

		// Custom code block rendering
		renderer.code = (code: string, language?: string) => {
			const lang = language || '';
			const escapedCode = code.replace(/</g, '&lt;').replace(/>/g, '&gt;');
			return `<div class="my-4"><div class="relative group"><pre class="bg-surface-900 rounded-xl p-4 overflow-x-auto"><code class="text-sm font-mono text-surface-200">${escapedCode}</code></pre>${lang ? `<div class="absolute top-2 right-2 px-2 py-0.5 bg-surface-800/80 rounded text-xs text-surface-500 font-mono">${lang}</div>` : ''}</div></div>`;
		};

		// Enhanced blockquote rendering
		renderer.blockquote = (quote: string) => {
			return `<blockquote class="border-l-3 border-surface-600/50 pl-4 py-2 my-4 bg-surface-900/50 rounded-r-lg italic text-surface-300">${quote}</blockquote>`;
		};

		// Enhanced list rendering
		renderer.list = (body: string, ordered: boolean) => {
			const tag = ordered ? 'ol' : 'ul';
			const listClass = ordered
				? 'list-decimal list-inside space-y-2 my-4 text-surface-200'
				: 'list-disc list-inside space-y-2 my-4 text-surface-200';
			return `<${tag} class="${listClass}">${body}</${tag}>`;
		};

		// Enhanced heading rendering
		renderer.heading = (text: string, level: number) => {
			const sizes = {
				1: 'text-2xl font-bold mt-8 mb-4 pb-2',
				2: 'text-xl font-semibold mt-6 mb-3 pb-2',
				3: 'text-lg font-semibold mt-5 mb-2',
				4: 'text-base font-semibold mt-4 mb-2'
			};
			const sizeClass = sizes[level as keyof typeof sizes] || 'text-base font-semibold mt-4 mb-2';
			return `<h${level} class="${sizeClass} text-surface-100 first:mt-0">${text}</h${level}>`;
		};

		// Enhanced paragraph rendering
		renderer.paragraph = (text: string) => {
			return `<p class="text-surface-200 leading-relaxed my-3 first:mt-0 last:mb-0">${text}</p>`;
		};

		// Enhanced strong rendering
		renderer.strong = (text: string) => {
			return `<strong class="font-semibold text-surface-100">${text}</strong>`;
		};

		// Enhanced link rendering
		renderer.link = (href: string, title: string | null, text: string) => {
			return `<a href="${href}" ${title ? `title="${title}"` : ''} class="text-blue-400 hover:text-blue-300 underline underline-offset-2 transition-colors" target="_blank" rel="noopener noreferrer">${text}</a>`;
		};

		// Enhanced table rendering
		renderer.table = (header: string, body: string) => {
			return `<div class="overflow-x-auto my-4"><table class="min-w-full border-collapse rounded-lg"><thead class="bg-surface-700/50">${header}</thead><tbody>${body}</tbody></table></div>`;
		};

		renderer.tablerow = (content: string) => {
			return `<tr>${content}</tr>`;
		};

		renderer.tablecell = (content: string, flags: { header: boolean; align?: string }) => {
			const tag = flags.header ? 'th' : 'td';
			const alignClass = flags.align ? `text-${flags.align}` : '';
			const cellClass = flags.header
				? `px-4 py-3 text-left text-xs font-semibold text-surface-300 uppercase tracking-wider ${alignClass}`
				: `px-4 py-3 text-sm text-surface-200 ${alignClass}`;
			return `<${tag} class="${cellClass}">${content}</${tag}>`;
		};

		// Enhanced horizontal rule
		renderer.hr = () => {
			return '<hr class="my-6 border-surface-700/30">';
		};

		// Standardized image rendering
		renderer.image = (href: string, title: string | null, text: string) => {
			const alt = text || '';
			const titleAttr = title ? `title="${title.replace(/"/g, '&quot;')}"` : '';

			// Standardized image wrapper with consistent styling
			return `
				<div class="markdown-image-container my-4 rounded-lg overflow-hidden bg-surface-700/30">
					<img
						src="${href.replace(/"/g, '&quot;')}"
						alt="${alt.replace(/"/g, '&quot;')}"
						${titleAttr}
						class="markdown-image w-full h-auto max-w-full transition-opacity duration-200 object-contain"
						loading="lazy"
					/>
					${alt ? `<div class="image-caption text-xs text-surface-500 font-mono mt-2 px-3 pb-2 text-center pt-2">${alt}</div>` : ''}
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
				headerIds: false,
				mangle: false,
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
	@reference "../../app.css";

	.formatted-message :global(p) {
		@apply text-surface-200 leading-relaxed my-3 first:mt-0 last:mb-0;
	}

	.formatted-message :global(code:not(pre code)) {
		@apply text-blue-400 bg-surface-800/80 px-1.5 py-0.5 rounded-md text-sm font-mono before:content-none after:content-none;
	}

	.formatted-message :global(pre) {
		@apply bg-surface-900 rounded-xl p-4 overflow-x-auto my-4;
	}

	.formatted-message :global(pre code) {
		@apply text-sm font-mono text-surface-200 bg-transparent p-0;
	}

	.formatted-message :global(ul),
	.formatted-message :global(ol) {
		@apply my-4 space-y-2;
	}

	.formatted-message :global(ul) {
		@apply list-disc list-inside space-y-1.5;
	}

	.formatted-message :global(ol) {
		@apply list-decimal list-inside space-y-1.5;
	}

	.formatted-message :global(li) {
		@apply text-surface-200 leading-relaxed;
	}

	.formatted-message :global(li > p) {
		@apply inline my-0;
	}

	.formatted-message :global(blockquote) {
		@apply border-l-4 border-surface-600/50 pl-4 py-2 my-4 bg-surface-900/50 rounded-r-lg italic text-surface-300;
	}

	.formatted-message :global(table) {
		@apply min-w-full border-collapse rounded-lg overflow-hidden my-4;
	}

	.formatted-message :global(thead) {
		@apply bg-surface-700/50;
	}

	.formatted-message :global(th) {
		@apply px-4 py-3 text-left text-xs font-semibold text-surface-300 uppercase tracking-wider;
	}

	.formatted-message :global(td) {
		@apply px-4 py-3 text-sm text-surface-200;
	}

	.formatted-message :global(tr) {
	}

	/* Enhanced text selection visibility */
	.formatted-message {
		-webkit-user-select: text;
		-moz-user-select: text;
		-ms-user-select: text;
		user-select: text;
	}

	.formatted-message :global(::selection) {
		background: rgba(255, 235, 59, 0.65); /* Yellow highlighter */
		color: inherit; /* Keep original text color */
		text-shadow: none;
	}

	.formatted-message :global(::-moz-selection) {
		background: rgba(255, 235, 59, 0.65); /* Yellow highlighter */
		color: inherit; /* Keep original text color */
		text-shadow: none;
	}

	/* Standardized image styling */
	.formatted-message :global(.markdown-image-container) {
		@apply relative my-4 rounded-lg overflow-hidden bg-surface-700/30;
	}

	.formatted-message :global(.markdown-image) {
		@apply w-full h-auto max-w-full;
		@apply transition-opacity duration-200;
		@apply object-contain;
		display: block;
	}

	.formatted-message :global(.image-caption) {
		@apply text-xs text-surface-500 font-mono mt-2 px-3 pb-2 text-center pt-2;
	}

	/* Ensure images don't break layout */
	.formatted-message :global(img) {
		max-width: 100%;
		height: auto;
	}

	/* Handle broken images */
	.formatted-message :global(img:not([src])) {
		display: none;
	}
</style>


