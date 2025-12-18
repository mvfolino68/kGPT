import { marked } from 'marked';
import type { MarkedOptions } from 'marked';

/**
 * Transform inline citation references [1], [2] etc into clickable badges.
 * These are clickable buttons that open the source drawer.
 */
function transformCitations(html: string): string {
	// Match citation patterns like [1], [2], [3] etc
	// Also matches ranges like [1,2] or [1, 2, 3]
	return html.replace(/\[(\d+(?:\s*,\s*\d+)*)\]/g, (match, indices) => {
		// Handle comma-separated indices like [1, 2, 3]
		const nums = indices.split(/\s*,\s*/);
		if (nums.length > 1) {
			const badges = nums.map((num: string) =>
				`<button type="button" class="citation-ref" data-citation-index="${num.trim()}">${num.trim()}</button>`
			);
			return badges.join('');
		}
		// Single citation - make it a button for accessibility and click handling
		return `<button type="button" class="citation-ref" data-citation-index="${indices.trim()}">${indices.trim()}</button>`;
	});
}

/**
 * Create a renderer with standardized image rendering
 */
function createRenderer() {
	const renderer = new marked.Renderer();

	// Standardized image rendering - matches FormattedMessage component
	renderer.image = (href: string, title: string | null, text: string) => {
		const alt = text || '';
		const titleAttr = title ? `title="${title.replace(/"/g, '&quot;')}"` : '';

		// Standardized image wrapper with consistent styling
		return `
			<div class="markdown-image-container my-4 rounded-lg overflow-hidden border border-surface-700/50 bg-surface-900/30 transition-all duration-200 hover:border-surface-600/50 hover:shadow-lg">
				<img
					src="${href.replace(/"/g, '&quot;')}"
					alt="${alt.replace(/"/g, '&quot;')}"
					${titleAttr}
					class="markdown-image w-full h-auto max-w-full transition-opacity duration-200 object-contain"
					loading="lazy"
				/>
				${alt ? `<div class="image-caption text-xs text-surface-500 font-mono mt-2 px-3 pb-2 text-center border-t border-surface-700/30 pt-2">${alt}</div>` : ''}
			</div>
		`;
	};

	return renderer;
}

/**
 * Safely render markdown content to HTML with styled citation references.
 */
export function renderMarkdown(content: string): string {
	if (!content) return '';
	try {
		const renderer = createRenderer();
		const options: MarkedOptions = {
			breaks: true,
			gfm: true,
			renderer
		};
		const html = marked.parse(content, options) as string;
		return transformCitations(html);
	} catch {
		return transformCitations(content.replace(/\n/g, '<br>'));
	}
}

/**
 * Render markdown without citation transformation (for previews etc)
 */
export function renderMarkdownPlain(content: string): string {
	if (!content) return '';
	try {
		return marked.parse(content, { breaks: true, gfm: true }) as string;
	} catch {
		return content.replace(/\n/g, '<br>');
	}
}
