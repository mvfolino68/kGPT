import type {
	DocumentSource,
	CollectionsResponse,
	VectorSearchResponse,
	VectorBrowseResponse,
	RAGPipelineInfo,
	RAGDemoResponse,
	ChunkResult,
	SyncStatusResponse,
	ChunkAnalytics,
	SourceType
} from '$lib/api';

export type {
	DocumentSource,
	CollectionsResponse,
	VectorSearchResponse,
	VectorBrowseResponse,
	RAGPipelineInfo,
	RAGDemoResponse,
	ChunkResult,
	SyncStatusResponse,
	ChunkAnalytics,
	SourceType
};

export type Tab = 'sources' | 'search' | 'browse' | 'pipeline';

export interface IngestionProgress {
	status: string;
	progress: number;
	stage: string;
	message: string;
	updated_at?: string;
	count?: number;
	pages?: number;
	pages_fetched?: number;
	pages_total?: number;
	pages_successful?: number;
	pages_processed?: number;
	documents_created?: number;
	chunks?: number;
	chunks_embedded?: number;
	error?: string;
	elapsed_seconds?: number;
}

export type DestructiveOperation = 'cleanup_orphans' | 'cleanup_stale' | 'purge_all' | null;

export interface SourceTypeOption {
	value: SourceType;
	label: string;
	description: string;
}

export const sourceTypeOptions: SourceTypeOption[] = [
	{ value: 'github', label: 'GitHub', description: 'Repository docs (public or private)' },
	{ value: 'file', label: 'File', description: 'Upload PDF, markdown, or text' },
	{ value: 'text', label: 'Raw Text', description: 'Paste raw text content' }
];

export function formatBytes(bytes: number): string {
	if (bytes === 0) return '—';
	const k = 1024;
	const sizes = ['B', 'KB', 'MB', 'GB'];
	const i = Math.floor(Math.log(bytes) / Math.log(k));
	return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

export function estimateStorageSize(vectors: number, dims: number): string {
	const vectorBytes = vectors * dims * 4;
	const metadataBytes = vectors * 500;
	return formatBytes(vectorBytes + metadataBytes);
}

export function getSimilarityColor(percent: number): string {
	if (percent >= 80) return 'text-emerald-400';
	if (percent >= 60) return 'text-lime-400';
	if (percent >= 40) return 'text-amber-400';
	return 'text-red-400';
}

export function getStatusColor(status: string): 'active' | 'warning' | 'error' | 'inactive' {
	const statusMap: Record<string, 'active' | 'warning' | 'error' | 'inactive'> = {
		indexed: 'active',
		indexing: 'warning',
		error: 'error',
		cancelled: 'inactive',
		pending: 'inactive'
	};
	return statusMap[status] || 'inactive';
}

