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
			return `<div class="my-4"><div class="relative group"><pre class="bg-surface-900 border border-white/5 rounded-xl p-4 overflow-x-auto shadow-xl"><code class="text-sm font-mono text-surface-200">${escapedCode}</code></pre>${lang ? `<div class="absolute top-2 right-2 px-2 py-0.5 bg-surface-800/80 border border-white/5 rounded text-xs text-surface-500 font-mono">${lang}</div>` : ''}</div></div>`;
		};

		// Enhanced blockquote rendering
		renderer.blockquote = (quote: string) => {
			return `<blockquote class="border-l-4 border-emerald-500/30 pl-4 py-2 my-4 bg-surface-900/50 rounded-r-lg italic text-surface-300">${quote}</blockquote>`;
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
				1: 'text-2xl font-bold mt-8 mb-4 pb-2 border-b border-white/5',
				2: 'text-xl font-semibold mt-6 mb-3 pb-2 border-b border-white/5',
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
			return `<div class="overflow-x-auto my-4"><table class="min-w-full border-collapse border border-white/10 rounded-lg"><thead class="bg-surface-800/50">${header}</thead><tbody>${body}</tbody></table></div>`;
		};

		renderer.tablerow = (content: string) => {
			return `<tr class="border-b border-white/5">${content}</tr>`;
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
			return '<hr class="my-6 border-white/5">';
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
		@apply text-emerald-400 bg-surface-800/80 px-1.5 py-0.5 rounded-md text-sm font-mono before:content-none after:content-none;
	}

	.formatted-message :global(pre) {
		@apply bg-surface-900 border border-white/5 rounded-xl p-4 overflow-x-auto shadow-xl my-4;
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
		@apply border-l-4 border-emerald-500/30 pl-4 py-2 my-4 bg-surface-900/50 rounded-r-lg italic text-surface-300;
	}

	.formatted-message :global(table) {
		@apply min-w-full border-collapse border border-white/10 rounded-lg overflow-hidden my-4;
	}

	.formatted-message :global(thead) {
		@apply bg-surface-800/50;
	}

	.formatted-message :global(th) {
		@apply px-4 py-3 text-left text-xs font-semibold text-surface-300 uppercase tracking-wider;
	}

	.formatted-message :global(td) {
		@apply px-4 py-3 text-sm text-surface-200 border-t border-white/5;
	}

	.formatted-message :global(tr) {
		@apply border-b border-white/5;
	}
</style>
