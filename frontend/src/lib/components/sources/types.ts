/**
 * Unified source type for all citations and references.
 *
 * This replaces the old separate Citation and WebSearchResult types
 * with a single, consistent data model that supports:
 * - RAG-retrieved documentation
 * - Web search results
 * - Cluster context information
 */

export interface SourceMetadata {
	/** Collection name for RAG docs */
	collection?: string;
	/** Query that found this source */
	search_query?: string;
	/** Published date for web results */
	published_date?: string;
	/** Rerank score if reranking was applied */
	rerank_score?: number;
	/** Original similarity score before reranking */
	similarity_score?: number;
}

export interface Source {
	/** Unique identifier for this source */
	id?: string;
	/** Display title */
	title: string;
	/** URL to the original source */
	url: string;
	/** Source type for visual distinction */
	type: 'doc' | 'web' | 'cluster';
	/** Preview of the content */
	content_preview?: string;
	/** Full content if available */
	content?: string;
	/** Highlighted excerpts from search results (for web sources) */
	highlights?: string[];
	/** Relevance score (0-1) */
	relevance_score?: number;
	/** Additional metadata */
	metadata?: SourceMetadata;
}

export interface SourceGroup {
	type: Source['type'];
	label: string;
	sources: Source[];
	icon: string;
	color: string;
}

/**
 * Group sources by type for organized display.
 */
export function groupSourcesByType(sources: Source[]): SourceGroup[] {
	const groups: Record<Source['type'], Source[]> = {
		doc: [],
		web: [],
		cluster: []
	};

	for (const source of sources) {
		if (groups[source.type]) {
			groups[source.type].push(source);
		}
	}

	const result: SourceGroup[] = [];

	if (groups.doc.length > 0) {
		result.push({
			type: 'doc',
			label: 'Documentation',
			sources: groups.doc,
			icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
			color: 'blue'
		});
	}

	if (groups.web.length > 0) {
		result.push({
			type: 'web',
			label: 'Web Search',
			sources: groups.web,
			icon: 'M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9',
			color: 'blue'
		});
	}

	if (groups.cluster.length > 0) {
		result.push({
			type: 'cluster',
			label: 'Cluster Info',
			sources: groups.cluster,
			icon: 'M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01',
			color: 'amber'
		});
	}

	return result;
}

/**
 * Convert legacy Citation format to unified Source format.
 * Handles both old URL strings and new structured citations with metadata.
 */
export function normalizeCitation(citation: unknown): Source {
	if (typeof citation === 'string') {
		// Legacy URL-only citation
		return {
			title: extractDomainFromUrl(citation),
			url: citation,
			type: 'doc'
		};
	}

	const c = citation as Record<string, unknown>;

	// Parse metadata if present
	let metadata: SourceMetadata | undefined;
	if (c.metadata && typeof c.metadata === 'object') {
		const m = c.metadata as Record<string, unknown>;
		metadata = {
			collection: m.collection as string | undefined,
			search_query: m.search_query as string | undefined,
			published_date: m.published_date as string | undefined,
			rerank_score: m.rerank_score as number | undefined,
			similarity_score: m.similarity_score as number | undefined
		};
	}

	// For relevance_score, prefer the main score but fall back to similarity_score
	// if the main score is 0 (which can happen when reranker returns 0)
	let relevance_score = c.relevance_score as number | undefined;
	if (relevance_score === 0 && metadata?.similarity_score) {
		relevance_score = metadata.similarity_score;
	}

	return {
		id: c.id as string | undefined,
		title: (c.title as string) || 'Untitled',
		url: (c.url as string) || '',
		type: (c.type as Source['type']) || 'doc',
		content_preview: c.content_preview as string | undefined,
		content: c.content as string | undefined,
		highlights: c.highlights as string[] | undefined,
		relevance_score,
		metadata
	};
}

function extractDomainFromUrl(url: string): string {
	try {
		return new URL(url).hostname.replace('www.', '');
	} catch {
		return url.split('/')[0] || 'Source';
	}
}
