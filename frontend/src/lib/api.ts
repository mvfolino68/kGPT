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

// Admin operation types
export interface InputField {
	name: string;
	label: string;
	field_type: 'text' | 'number' | 'select';
	required: boolean;
	default?: string | number | null;
	placeholder?: string;
	hint?: string;
	options?: string[];
}

export interface AvailableOperation {
	id: string;
	label: string;
	icon: string;
}

export interface PartitionDetail {
	partition: number;
	leader: number | null;
	replicas: number[];
	isrs: number[];
}

export interface AdminOperationResult {
	success: boolean;
	operation?: string;
	operation_title?: string;  // Human-readable title
	pending?: boolean;  // All info gathered, ready for confirmation
	needs_info?: boolean;  // Need more input from user
	unclear?: boolean;  // Couldn't determine the operation
	params?: Record<string, unknown>;
	input_fields?: InputField[];  // Structured input fields
	available_operations?: AvailableOperation[];  // For unclear status
	guidance_message?: string;  // Helpful guidance text
	confirmation_message?: string;
	warning_level?: 'low' | 'medium' | 'high';
	warning_message?: string;  // Warning for high-risk operations
	message?: string;
	error?: string;
	topic?: string;
	group_id?: string;
	partitions?: number | PartitionDetail[];  // int for create, list for describe
	partition_count?: number;
	replication_factor?: number;
	configuration?: Record<string, string>;  // Topic config from describe
	all_configs?: Record<string, { value: string; is_default: boolean; is_read_only: boolean }>;
}

// ============================================================================
// Agent Activity Types (for educational pipeline visibility)
// ============================================================================

export type AgentName = 'router' | 'retrieval' | 'kafka' | 'admin' | 'web_search' | 'synthesis' | 'error';
export type AgentStatus = 'pending' | 'started' | 'completed' | 'error';

export interface AgentEvent {
	agent: AgentName;
	status: AgentStatus;
	description?: string;
	duration_ms?: number;
	result?: Record<string, unknown>;
}

export interface RoutingDecision {
	route: string;
	reasoning: string;
	sub_goals: string[];
	needs_cluster: boolean;
	needs_retrieval: boolean;
	needs_web_search: boolean;
	needs_admin: boolean;
}

export interface RetrievalResultItem {
	source: string;
	source_name: string;
	content_preview: string;
	similarity_score: number;
	rerank_score: number | null;
	collection: string;
	search_query: string | null;
}

export interface RetrievalResults {
	docs: RetrievalResultItem[];
	total: number;
	queries_expanded: number;
	reranked: boolean;
	reranking_model: string | null;
}

export interface WebSearchResultItem {
	title: string;
	url: string;
	highlights?: string[];
}

export interface WebSearchResults {
	results: WebSearchResultItem[];
	total: number;
}

export interface AdminOperationRequest {
	operation: string;
	params: Record<string, unknown>;
}

// Citation can be either a simple URL string or a full object with metadata
export interface CitationMetadata {
	collection?: string;
	similarity_score?: number;
	rerank_score?: number;
	published_date?: string;
	search_query?: string;
}

export interface CitationObject {
	title: string;
	url: string;
	type: 'doc' | 'web' | 'cluster';
	content_preview?: string;
	relevance_score?: number;
	metadata?: CitationMetadata;
}

export type Citation = string | CitationObject;

export interface ChatResponse {
	answer: string;
	citations: Citation[];
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

export interface AgentTraceData {
	routing_decision?: RoutingDecision;
	retrieval_results?: RetrievalResults;
	validation_results?: {
		validated: number;
		filtered: number;
		results: Array<{
			source: string;
			is_relevant: boolean;
			confidence: number;
			reasoning?: string;
		}>;
	};
	web_search_results?: WebSearchResults;
	agent_timeline: Array<{
		agent: AgentName;
		status: AgentStatus;
		description?: string;
		duration_ms?: number;
		result?: Record<string, unknown>;
	}>;
}

export interface ChatSessionMessage {
	id: number;
	session_id: string;
	role: 'user' | 'assistant';
	content: string;
	citations: Citation[];
	actions?: SuggestedAction[];
	agent_trace?: AgentTraceData;
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

export type SourceType = 'url' | 'github' | 'file' | 'text' | 'sitemap';

export interface IngestRequest {
	source_type: SourceType;
	name?: string; // Optional - will be auto-generated if empty and auto_name is true
	url?: string;
	collection_name?: string;
	auto_name?: boolean; // Default true - use AI to generate a smart name
}

export interface NameSuggestionRequest {
	url?: string;
	content?: string;
	source_type?: SourceType;
}

export interface NameSuggestionResponse {
	suggestions: string[];
	smart_name: string | null;
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

// Enhanced cluster details for dashboard
export interface BrokerInfo {
	id: number;
	host: string;
	port: number;
	is_controller: boolean;
	partition_count: number;
	leader_count: number;
}

export interface TopicInfo {
	name: string;
	partition_count: number;
	replication_factor: number;
	leader_distribution: Record<number, number>;
	is_internal: boolean;
	under_replicated: boolean;
}

export interface ConsumerGroupInfo {
	group_id: string;
	state: string;
	protocol_type: string | null;
	member_count: number;
	coordinator_id: number | null;
	topics: string[];
}

export interface ClusterDetailsResponse {
	connected: boolean;
	cluster_id: string | null;
	controller_id: number | null;
	brokers: BrokerInfo[];
	broker_count: number;
	topics: TopicInfo[];
	topic_count: number;
	total_partitions: number;
	under_replicated_count: number;
	consumer_groups: ConsumerGroupInfo[];
	consumer_group_count: number;
	error: string | null;
}

export interface KeyStatus {
	configured: boolean;
	source: 'env' | 'db' | null;
	valid: boolean | null;
}

export interface Settings {
	llm_provider: string;
	llm_model: string;
	embedding_provider: string;
	embedding_model: string;
	// API keys for updates
	openai_api_key?: string;
	exa_api_key?: string;
	cohere_api_key?: string;
	huggingface_token?: string;
	// Web search toggle
	web_search_enabled?: boolean;
	// Key status
	openai_key?: KeyStatus;
	exa_key?: KeyStatus;
	cohere_key?: KeyStatus;
	huggingface_token_status?: KeyStatus;
	// Legacy fields
	has_openai_key?: boolean;
	has_exa_key?: boolean;
	has_cohere_key?: boolean;
	has_huggingface_token?: boolean;
}

export interface ValidateKeyResponse {
	valid: boolean;
	provider: string;
	message: string | null;
	models: string[];
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

// Admin Operation Execution
export async function executeAdminOperation(request: AdminOperationRequest): Promise<AdminOperationResult> {
	const response = await fetch(`${API_BASE}/chat/admin/execute`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(request)
	});
	if (!response.ok) throw new Error(`Admin operation failed: ${response.statusText}`);
	return response.json();
}

// Documents API
export async function getDocuments(): Promise<DocumentSource[]> {
	const response = await fetch(`${API_BASE}/documents/sources`);
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

export async function suggestName(request: NameSuggestionRequest): Promise<NameSuggestionResponse> {
	const response = await fetch(`${API_BASE}/documents/sources/suggest-name`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(request)
	});
	if (!response.ok) throw new Error(`Name suggestion failed: ${response.statusText}`);
	return response.json();
}

export async function ingestDocument(request: IngestRequest): Promise<IngestResponse> {
	const response = await fetch(`${API_BASE}/documents/sources/ingest`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(request)
	});
	if (!response.ok) throw new Error(`Ingest failed: ${response.statusText}`);
	return response.json();
}

export async function getIngestionStatus(sourceId: number): Promise<IngestionStatus> {
	const response = await fetch(`${API_BASE}/documents/sources/${sourceId}/status`);
	if (!response.ok) throw new Error(`Failed to get status: ${response.statusText}`);
	return response.json();
}

export async function deleteDocument(id: number): Promise<void> {
	const response = await fetch(`${API_BASE}/documents/sources/${id}`, { method: 'DELETE' });
	if (!response.ok) throw new Error(`Delete failed: ${response.statusText}`);
}

export async function cancelIngestion(id: number): Promise<void> {
	const response = await fetch(`${API_BASE}/documents/sources/${id}/cancel`, { method: 'POST' });
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

export interface HNSWConfig {
	m: number | null;
	ef_construct: number | null;
	full_scan_threshold: number | null;
	on_disk: boolean;
}

export interface CollectionStats {
	name: string;
	vectors_count: number;
	points_count: number;
	indexed_vectors_count: number;
	segments_count: number;
	status: string;
	optimizer_status: string;
	dimensions: number;
	distance_metric: string;
	on_disk_vectors: boolean | null;
	on_disk_payload: boolean | null;
	disk_data_size: number;
	ram_data_size: number;
	hnsw_config: HNSWConfig | null;
	optimizer_config: Record<string, unknown> | null;
	quantization_config: Record<string, unknown> | null;
	payload_schema: Record<string, unknown> | null;
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
	const response = await fetch(`${API_BASE}/documents/rag/info`);
	if (!response.ok) throw new Error(`Failed to get RAG info: ${response.statusText}`);
	return response.json();
}

export async function runRAGDemo(query: string): Promise<RAGDemoResponse> {
	const params = new URLSearchParams({ query });
	const response = await fetch(`${API_BASE}/documents/rag/demo?${params}`);
	if (!response.ok) throw new Error(`Failed to run RAG demo: ${response.statusText}`);
	return response.json();
}

// Agent Graph Info (Educational)
export interface AgentGraphNode {
	name: string;
	label: string;
	description: string;
	icon: string;
	color: string;
}

export interface AgentGraphEdge {
	from_node: string;
	to_node: string;
	condition: string | null;
}

export interface AgentGraphInfo {
	nodes: AgentGraphNode[];
	edges: AgentGraphEdge[];
	entry_point: string;
	description: string;
}

export async function getAgentGraph(): Promise<AgentGraphInfo> {
	const response = await fetch(`${API_BASE}/chat/graph`);
	if (!response.ok) throw new Error(`Failed to get agent graph: ${response.statusText}`);
	return response.json();
}

// ============================================================================
// Sync and Cleanup APIs
// ============================================================================

export interface SourceSyncStatus {
	id: number;
	name: string;
	collection_name: string;
	db_status: string;
	db_count: number;
	qdrant_count: number;
	in_qdrant: boolean;
	synced: boolean;
}

export interface SyncStatusResponse {
	synced: boolean;
	total_vectors: number;
	db_sources_count: number;
	qdrant_collections_count: number;
	orphaned_collections: string[];
	missing_sources: string[];
	source_status: SourceSyncStatus[];
}

export interface CleanupResult {
	status: string;
	orphans_found?: number;
	total_vectors_deleted?: number;
	deleted_sources?: Array<{ name: string; vectors_deleted?: number; error?: string }>;
	entries_cleaned?: number;
	cleaned?: Array<{ id: number; name: string; status: string }>;
}

export async function getSyncStatus(): Promise<SyncStatusResponse> {
	const response = await fetch(`${API_BASE}/documents/sync/status`);
	if (!response.ok) throw new Error(`Failed to get sync status: ${response.statusText}`);
	return response.json();
}

export async function cleanupOrphanVectors(): Promise<CleanupResult> {
	const response = await fetch(`${API_BASE}/documents/sync/cleanup-orphans`, {
		method: 'POST'
	});
	if (!response.ok) throw new Error(`Failed to cleanup orphans: ${response.statusText}`);
	return response.json();
}

export async function cleanupStaleEntries(): Promise<CleanupResult> {
	const response = await fetch(`${API_BASE}/documents/sync/cleanup-stale`, {
		method: 'POST'
	});
	if (!response.ok) throw new Error(`Failed to cleanup stale entries: ${response.statusText}`);
	return response.json();
}

export async function purgeAllData(): Promise<{ status: string; db_entries_deleted: number; vectors_deleted: number }> {
	const response = await fetch(`${API_BASE}/documents/sync/purge-all`, {
		method: 'DELETE'
	});
	if (!response.ok) throw new Error(`Failed to purge data: ${response.statusText}`);
	return response.json();
}

// ============================================================================
// Analytics APIs
// ============================================================================

export interface ChunkAnalytics {
	collection: string;
	total_vectors: number;
	total_sampled: number;
	chunk_size_stats: {
		avg_chars: number;
		min_chars: number;
		max_chars: number;
		avg_tokens_estimate: number;
	};
	size_distribution: Record<string, number>;
	sources: Record<string, number>;
	source_types: Record<string, number>;
	index_health: {
		indexed_vectors: number;
		segments: number;
		optimizer_status: string;
	};
}

export interface SearchQualityResult {
	query: string;
	results_found: number;
	quality_metrics: {
		avg_similarity: number;
		top_score: number;
		score_spread: number;
		score_variance: number;
	};
	sources_matched: string[];
	expected_source_match: { rank: number; score: number } | null;
	top_3_preview: Array<{
		rank: number;
		score: number;
		source: string;
		preview: string;
	}>;
}

export async function getChunkAnalytics(collection?: string): Promise<ChunkAnalytics> {
	const params = new URLSearchParams();
	if (collection) params.append('collection', collection);
	const response = await fetch(`${API_BASE}/documents/analytics/chunks?${params}`);
	if (!response.ok) throw new Error(`Failed to get analytics: ${response.statusText}`);
	return response.json();
}

export async function testSearchQuality(query: string, expectedSource?: string): Promise<SearchQualityResult> {
	const params = new URLSearchParams({ query });
	if (expectedSource) params.append('expected_source', expectedSource);
	const response = await fetch(`${API_BASE}/documents/analytics/search-quality?${params}`);
	if (!response.ok) throw new Error(`Failed to test search: ${response.statusText}`);
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

export async function getClusterDetails(): Promise<ClusterDetailsResponse> {
	const response = await fetch(`${API_BASE}/cluster/details`);
	if (!response.ok) throw new Error(`Failed to get cluster details: ${response.statusText}`);
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

export async function validateApiKey(
	provider: string,
	apiKey: string,
	options?: { ollama_host?: string }
): Promise<ValidateKeyResponse> {
	const response = await fetch(`${API_BASE}/settings/validate-key`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ provider, api_key: apiKey, ...options })
	});
	if (!response.ok) throw new Error(`Validation failed: ${response.statusText}`);
	return response.json();
}

// Health API
export async function checkHealth(): Promise<HealthResponse> {
	const response = await fetch(`${API_BASE}/health`);
	if (!response.ok) throw new Error(`Health check failed: ${response.statusText}`);
	return response.json();
}

// ============================================================================
// Operations Discovery API
// ============================================================================

export interface OperationParam {
	name: string;
	label: string;
	param_type: string;
	required: boolean;
	default: unknown;
	placeholder: string;
	hint: string;
	options: string[];
}

export interface KafkaOperation {
	id: string;
	name: string;
	description: string;
	category: string;
	operation_type: 'read' | 'write' | 'destructive';
	icon: string;
	params: OperationParam[];
	requires_confirmation: boolean;
	available?: boolean;
	unavailable_reason?: string;
}

export interface OperationsSummary {
	total_operations: number;
	read_operations: number;
	write_operations: number;
	destructive_operations: number;
	categories: string[];
}

export interface OperationsResponse {
	cluster_connected: boolean;
	operations: KafkaOperation[];
	summary: OperationsSummary;
}

export interface OperationsByCategory {
	categories: Record<string, KafkaOperation[]>;
}

export interface OperationExample {
	category: string;
	examples: string[];
}

export interface OperationSuggestion {
	operation_id: string;
	operation_name: string;
	suggested_prompt: string;
	type: 'follow_up' | 'explore' | 'common';
}

export interface SuggestionsResponse {
	suggestions: OperationSuggestion[];
	cluster_connected: boolean;
}

/**
 * Get all available Kafka admin operations.
 * Returns operations with availability status based on cluster connection.
 */
export async function getAvailableOperations(): Promise<OperationsResponse> {
	const response = await fetch(`${API_BASE}/cluster/operations`);
	if (!response.ok) throw new Error(`Failed to get operations: ${response.statusText}`);
	return response.json();
}

/**
 * Get operations grouped by category.
 */
export async function getOperationsByCategory(): Promise<OperationsByCategory> {
	const response = await fetch(`${API_BASE}/cluster/operations/by-category`);
	if (!response.ok) throw new Error(`Failed to get operations: ${response.statusText}`);
	return response.json();
}

/**
 * Get example prompts for each operation category.
 */
export async function getOperationExamples(): Promise<{ examples: OperationExample[] }> {
	const response = await fetch(`${API_BASE}/cluster/operations/examples`);
	if (!response.ok) throw new Error(`Failed to get examples: ${response.statusText}`);
	return response.json();
}

/**
 * Get suggested next operations based on context.
 */
export async function getOperationSuggestions(
	lastOperation?: string,
	lastSuccess: boolean = true
): Promise<SuggestionsResponse> {
	const params = new URLSearchParams();
	if (lastOperation) params.set('last_operation', lastOperation);
	params.set('last_success', lastSuccess.toString());

	const response = await fetch(`${API_BASE}/cluster/operations/suggestions?${params}`);
	if (!response.ok) throw new Error(`Failed to get suggestions: ${response.statusText}`);
	return response.json();
}
