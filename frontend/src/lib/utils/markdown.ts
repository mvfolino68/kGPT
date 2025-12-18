import { marked } from 'marked';

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
 * Safely render markdown content to HTML with styled citation references.
 */
export function renderMarkdown(content: string): string {
	if (!content) return '';
	try {
		const html = marked.parse(content, { breaks: true, gfm: true }) as string;
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
