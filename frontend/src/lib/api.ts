/**
 * API client for kGPT backend
 */

const API_BASE = '/api';

export interface Message {
	role: 'user' | 'assistant';
	content: string;
}

export interface ChatRequest {
	message: string;
	history: Message[];
	session_id?: string;
}

// Suggested action that can be taken after a response
export interface SuggestedAction {
	id: string;
	label: string;
	type: 'query' | 'operation' | 'navigate';
	value: string;
	icon?: string;
	description?: string;
}

// Cluster operation result embedded in response
export interface ClusterOperationResult {
	operation: string;
	success: boolean;
	data?: Record<string, unknown>;
	error?: string;
}

export interface ChatResponse {
	answer: string;
	citations: string[];
	error?: string;
	actions?: SuggestedAction[];
	cluster_context?: {
		brokers?: number;
		topics?: string[];
		consumer_groups?: string[];
		cluster_id?: string;
	};
	operation_result?: ClusterOperationResult;
}

export interface ChatSession {
	id: string;
	title: string;
	created_at: string;
	updated_at: string;
}

export interface ChatSessionMessage {
	id: number;
	session_id: string;
	role: 'user' | 'assistant';
	content: string;
	citations: string[];
	actions?: SuggestedAction[];
	created_at: string;
}

export interface ChatSessionWithMessages {
	session: ChatSession;
	messages: ChatSessionMessage[];
}

export interface DocumentSource {
	id: number;
	name: string;
	source_type: string;
	url?: string;
	collection_name: string;
	document_count: number;
	status: string;
	created_at: string;
	indexed_at?: string;
}

export interface IngestRequest {
	source_type: 'sitemap' | 'github' | 'url' | 'upload';
	name: string;
	url?: string;
	collection_name?: string;
}

export interface KafkaCluster {
	id: number;
	name: string;
	bootstrap_servers: string;
	security_protocol: string;
	is_active: boolean;
}

export interface ClusterInfo {
	connected: boolean;
	cluster_id?: string;
	brokers?: number;
	topics?: string[];
	consumer_groups?: string[];
}

export interface Settings {
	llm_provider: string;
	llm_model: string;
	embedding_provider: string;
	embedding_model: string;
	openai_api_key?: string;
	anthropic_api_key?: string;
	openrouter_api_key?: string;
	cohere_api_key?: string;
	huggingface_token?: string;
	ollama_host?: string;
	has_openai_key?: boolean;
	has_anthropic_key?: boolean;
	has_openrouter_key?: boolean;
	has_cohere_key?: boolean;
	has_huggingface_token?: boolean;
}

export interface HealthResponse {
	status: string;
	version: string;
	qdrant_connected: boolean;
	kafka_connected: boolean;
}

// Chat API
export async function sendMessage(request: ChatRequest): Promise<ChatResponse> {
	const response = await fetch(`${API_BASE}/chat`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(request)
	});
	if (!response.ok) throw new Error(`Chat failed: ${response.statusText}`);
	return response.json();
}

export async function* streamMessage(
	request: ChatRequest
): AsyncGenerator<{ type: string; data: string | string[] }> {
	const response = await fetch(`${API_BASE}/chat/stream`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(request)
	});

	if (!response.ok) throw new Error(`Stream failed: ${response.statusText}`);
	if (!response.body) throw new Error('No response body');

	const reader = response.body.getReader();
	const decoder = new TextDecoder();
	let buffer = '';

	while (true) {
		const { done, value } = await reader.read();
		if (done) break;

		buffer += decoder.decode(value, { stream: true });
		const lines = buffer.split('\n');
		buffer = lines.pop() || '';

		for (const line of lines) {
			if (line.startsWith('data: ')) {
				try {
					const data = JSON.parse(line.slice(6));
					yield data;
				} catch {
					// Skip malformed JSON
				}
			}
		}
	}
}

// Chat Session API
export async function getChatSessions(): Promise<ChatSession[]> {
	const response = await fetch(`${API_BASE}/chat/sessions`);
	if (!response.ok) throw new Error(`Failed to get sessions: ${response.statusText}`);
	const data = await response.json();
	return data.sessions;
}

export async function createChatSession(title: string = 'New Chat'): Promise<ChatSession> {
	const response = await fetch(`${API_BASE}/chat/sessions`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ title })
	});
	if (!response.ok) throw new Error(`Failed to create session: ${response.statusText}`);
	return response.json();
}

export async function getChatSession(sessionId: string): Promise<ChatSessionWithMessages> {
	const response = await fetch(`${API_BASE}/chat/sessions/${sessionId}`);
	if (!response.ok) throw new Error(`Failed to get session: ${response.statusText}`);
	return response.json();
}

export async function updateChatSession(sessionId: string, title: string): Promise<ChatSession> {
	const response = await fetch(`${API_BASE}/chat/sessions/${sessionId}`, {
		method: 'PUT',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ title })
	});
	if (!response.ok) throw new Error(`Failed to update session: ${response.statusText}`);
	return response.json();
}

export async function deleteChatSession(sessionId: string): Promise<void> {
	const response = await fetch(`${API_BASE}/chat/sessions/${sessionId}`, { method: 'DELETE' });
	if (!response.ok) throw new Error(`Failed to delete session: ${response.statusText}`);
}

export async function clearAllChatSessions(): Promise<void> {
	const response = await fetch(`${API_BASE}/chat/sessions`, { method: 'DELETE' });
	if (!response.ok) throw new Error(`Failed to clear sessions: ${response.statusText}`);
}

// Documents API
export async function getDocuments(): Promise<DocumentSource[]> {
	const response = await fetch(`${API_BASE}/documents`);
	if (!response.ok) throw new Error(`Failed to get documents: ${response.statusText}`);
	const data = await response.json();
	return data.sources;
}

export interface IngestResponse {
	source_id: number;
	status: string;
	message: string;
}

export interface IngestionStatus {
	status: string;
	progress: number;
	stage: string;
	message: string;
	updated_at?: string;
	count?: number;
	pages?: number;
	pages_loaded?: number;
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

export async function ingestDocument(request: IngestRequest): Promise<IngestResponse> {
	const response = await fetch(`${API_BASE}/documents/ingest`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(request)
	});
	if (!response.ok) throw new Error(`Ingest failed: ${response.statusText}`);
	return response.json();
}

export async function getIngestionStatus(sourceId: number): Promise<IngestionStatus> {
	const response = await fetch(`${API_BASE}/documents/${sourceId}/status`);
	if (!response.ok) throw new Error(`Failed to get status: ${response.statusText}`);
	return response.json();
}

export async function deleteDocument(id: number): Promise<void> {
	const response = await fetch(`${API_BASE}/documents/${id}`, { method: 'DELETE' });
	if (!response.ok) throw new Error(`Delete failed: ${response.statusText}`);
}

export async function cancelIngestion(id: number): Promise<void> {
	const response = await fetch(`${API_BASE}/documents/${id}/cancel`, { method: 'POST' });
	if (!response.ok) throw new Error(`Cancel failed: ${response.statusText}`);
}

// ============================================================================
// Vector Search & Collection APIs
// ============================================================================

export interface ChunkResult {
	content: string;
	content_preview: string;
	metadata: Record<string, unknown>;
	similarity_score: number;
	similarity_percent: number;
	source: string;
	source_name: string;
	chunk_index?: number;
}

export interface VectorSearchResponse {
	chunks: ChunkResult[];
	total: number;
	query: string;
	collection: string | null;
}

export interface CollectionStats {
	name: string;
	vectors_count: number;
	points_count: number;
	indexed_vectors_count: number;
	status: string;
	dimensions: number;
	distance_metric: string;
	disk_data_size: number;
	ram_data_size: number;
}

export interface CollectionsResponse {
	collections: CollectionStats[];
	total_vectors: number;
	total_collections: number;
}

export interface VectorPoint {
	id: string;
	payload: Record<string, unknown>;
	vector_preview?: number[];
	vector_dimensions?: number;
}

export interface VectorBrowseResponse {
	points: VectorPoint[];
	next_offset: string | null;
	total_count: number;
	collection: string;
}

export interface EmbeddingResponse {
	text: string;
	vector: number[];
	dimensions: number;
	model: string;
}

export interface RAGPipelineStage {
	name: string;
	description: string;
	example?: string;
}

export interface RAGPipelineInfo {
	pipeline_stages: RAGPipelineStage[];
	retrieval_config: Record<string, unknown>;
	embedding_config: Record<string, unknown>;
	reranking_available: boolean;
	hybrid_search_enabled: boolean;
}

export interface RAGDemoStep {
	step: number;
	name: string;
	input?: unknown;
	output?: unknown;
	description?: string;
	error?: string;
}

export interface RAGDemoResponse {
	query: string;
	pipeline_steps: RAGDemoStep[];
	total_steps: number;
}

// Vector Search
export async function searchDocuments(
	query: string,
	options: {
		k?: number;
		collection?: string;
		source?: string;
	} = {}
): Promise<VectorSearchResponse> {
	const params = new URLSearchParams({ q: query });
	if (options.k) params.set('k', options.k.toString());
	if (options.collection) params.set('collection', options.collection);
	if (options.source) params.set('source', options.source);

	const response = await fetch(`${API_BASE}/documents/search?${params}`);
	if (!response.ok) throw new Error(`Search failed: ${response.statusText}`);
	return response.json();
}

// Collection Management
export async function getCollections(): Promise<CollectionsResponse> {
	const response = await fetch(`${API_BASE}/documents/collections`);
	if (!response.ok) throw new Error(`Failed to get collections: ${response.statusText}`);
	return response.json();
}

export async function getCollection(name: string): Promise<CollectionStats> {
	const response = await fetch(`${API_BASE}/documents/collections/${name}`);
	if (!response.ok) throw new Error(`Failed to get collection: ${response.statusText}`);
	return response.json();
}

export async function deleteCollection(name: string): Promise<void> {
	const response = await fetch(`${API_BASE}/documents/collections/${name}`, {
		method: 'DELETE'
	});
	if (!response.ok) throw new Error(`Failed to delete collection: ${response.statusText}`);
}

export async function getCollectionSources(name: string): Promise<{ sources: string[]; count: number }> {
	const response = await fetch(`${API_BASE}/documents/collections/${name}/sources`);
	if (!response.ok) throw new Error(`Failed to get sources: ${response.statusText}`);
	return response.json();
}

// Vector Browsing
export async function browseVectors(options: {
	collection?: string;
	limit?: number;
	offset?: string;
	source?: string;
	withVectors?: boolean;
}): Promise<VectorBrowseResponse> {
	const params = new URLSearchParams();
	if (options.collection) params.set('collection', options.collection);
	if (options.limit) params.set('limit', options.limit.toString());
	if (options.offset) params.set('offset', options.offset);
	if (options.source) params.set('source', options.source);
	if (options.withVectors) params.set('with_vectors', 'true');

	const response = await fetch(`${API_BASE}/documents/vectors/browse?${params}`);
	if (!response.ok) throw new Error(`Failed to browse vectors: ${response.statusText}`);
	return response.json();
}

export async function getVector(
	pointId: string,
	collection?: string,
	withVector: boolean = true
): Promise<VectorPoint & { vector?: number[] }> {
	const params = new URLSearchParams();
	if (collection) params.set('collection', collection);
	params.set('with_vector', withVector.toString());

	const response = await fetch(`${API_BASE}/documents/vectors/${pointId}?${params}`);
	if (!response.ok) throw new Error(`Failed to get vector: ${response.statusText}`);
	return response.json();
}

export async function deleteVectorsBySource(
	sourceName: string,
	collection?: string
): Promise<{ deleted_count: number }> {
	const params = new URLSearchParams();
	if (collection) params.set('collection', collection);

	const response = await fetch(
		`${API_BASE}/documents/vectors/by-source/${encodeURIComponent(sourceName)}?${params}`,
		{ method: 'DELETE' }
	);
	if (!response.ok) throw new Error(`Failed to delete vectors: ${response.statusText}`);
	return response.json();
}

// Embedding APIs (Educational)
export async function generateEmbedding(text: string): Promise<EmbeddingResponse> {
	const response = await fetch(`${API_BASE}/documents/embed`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ text })
	});
	if (!response.ok) throw new Error(`Failed to generate embedding: ${response.statusText}`);
	return response.json();
}

export async function compareEmbeddings(
	text1: string,
	text2: string
): Promise<{
	text1: string;
	text2: string;
	cosine_similarity: number;
	similarity_percent: number;
	interpretation: string;
}> {
	const params = new URLSearchParams({ text1, text2 });
	const response = await fetch(`${API_BASE}/documents/embed/compare?${params}`, {
		method: 'POST'
	});
	if (!response.ok) throw new Error(`Failed to compare embeddings: ${response.statusText}`);
	return response.json();
}

// RAG Pipeline Info (Educational)
export async function getRAGPipelineInfo(): Promise<RAGPipelineInfo> {
	const response = await fetch(`${API_BASE}/documents/rag/pipeline`);
	if (!response.ok) throw new Error(`Failed to get RAG info: ${response.statusText}`);
	return response.json();
}

export async function runRAGDemo(query: string): Promise<RAGDemoResponse> {
	const params = new URLSearchParams({ query });
	const response = await fetch(`${API_BASE}/documents/rag/demo?${params}`);
	if (!response.ok) throw new Error(`Failed to run RAG demo: ${response.statusText}`);
	return response.json();
}

// Cluster API
export async function getClusters(): Promise<KafkaCluster[]> {
	const response = await fetch(`${API_BASE}/cluster`);
	if (!response.ok) throw new Error(`Failed to get clusters: ${response.statusText}`);
	const data = await response.json();
	return data.available_clusters || [];
}

export async function getClusterInfo(): Promise<ClusterInfo> {
	const response = await fetch(`${API_BASE}/cluster/info`);
	if (!response.ok) throw new Error(`Failed to get cluster info: ${response.statusText}`);
	return response.json();
}

export async function connectCluster(cluster: Partial<KafkaCluster>): Promise<{ success: boolean }> {
	const response = await fetch(`${API_BASE}/cluster/connect`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(cluster)
	});
	if (!response.ok) throw new Error(`Connect failed: ${response.statusText}`);
	return response.json();
}

export async function disconnectCluster(): Promise<void> {
	const response = await fetch(`${API_BASE}/cluster/disconnect`, { method: 'POST' });
	if (!response.ok) throw new Error(`Disconnect failed: ${response.statusText}`);
}

// Settings API
export async function getSettings(): Promise<Settings> {
	const response = await fetch(`${API_BASE}/settings`);
	if (!response.ok) throw new Error(`Failed to get settings: ${response.statusText}`);
	return response.json();
}

export async function updateSettings(settings: Partial<Settings>): Promise<Settings> {
	const response = await fetch(`${API_BASE}/settings`, {
		method: 'PUT',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(settings)
	});
	if (!response.ok) throw new Error(`Update failed: ${response.statusText}`);
	return response.json();
}

export async function getAvailableModels(provider: string): Promise<string[]> {
	const response = await fetch(`${API_BASE}/settings/models/${provider}`);
	if (!response.ok) throw new Error(`Failed to get models: ${response.statusText}`);
	const data = await response.json();
	return data.models;
}

// Health API
export async function checkHealth(): Promise<HealthResponse> {
	const response = await fetch(`${API_BASE}/health`);
	if (!response.ok) throw new Error(`Health check failed: ${response.statusText}`);
	return response.json();
}
