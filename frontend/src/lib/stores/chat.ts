import { writable, derived } from 'svelte/store';
import type { Message, ChatSession, ChatSessionMessage, SuggestedAction, ClusterOperationResult, Citation, CitationObject } from '$lib/api';
import {
	getChatSessions,
	createChatSession,
	getChatSession,
	deleteChatSession,
	updateChatSession,
	clearAllChatSessions
} from '$lib/api';

// Re-export Citation types for consumers
export type { Citation, CitationObject };

// ============================================================================
// Admin Operation Types
// ============================================================================

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
	executed?: boolean;  // True if operation was executed (read operations)
	pending?: boolean;  // True if awaiting user confirmation
	needs_info?: boolean;  // True if we need more input from user
	unclear?: boolean;  // True if AI couldn't determine the operation
	operation?: string;
	operation_name?: string;  // Human-readable operation name
	operation_title?: string;  // Human-readable title (legacy)
	params?: Record<string, unknown>;  // Parameters for pending operations
	data?: Record<string, unknown>;  // Result data from executed operations
	input_fields?: InputField[];  // Structured input fields to show
	guidance_message?: string;  // Helpful guidance text
	available_operations?: AvailableOperation[];  // For unclear status
	confirmation_message?: string;  // What will happen if confirmed
	warning_level?: 'low' | 'medium' | 'high';  // Risk level for UI styling
	warning_message?: string;  // Warning for high-risk operations
	code_executed?: string;  // Python code that was executed
	code_preview?: string;  // Python code preview for pending operations
	topic?: string;
	group_id?: string;
	message?: string;
	error?: string;
	partitions?: number | PartitionDetail[];  // int for create, list for describe
	partition_count?: number;
	replication_factor?: number;
	configuration?: Record<string, string>;  // Topic config from describe
	all_configs?: Record<string, { value: string; is_default: boolean; is_read_only: boolean }>;
}

// ============================================================================
// Agent Activity Types (for educational pipeline visibility)
// ============================================================================

export type AgentName = 'router' | 'retrieval' | 'kafka' | 'admin' | 'validation' | 'synthesis' | 'error';
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

export interface ValidationResultItem {
	source: string;
	is_relevant: boolean;
	confidence: number;
	reasoning?: string;
}

export interface ValidationResults {
	validated: number;
	filtered: number;
	results: ValidationResultItem[];
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

export interface AgentActivity {
	agent: AgentName;
	status: AgentStatus;
	description?: string;
	startTime?: number;
	endTime?: number;
	duration_ms?: number;
	result?: Record<string, unknown>;
}

export interface MessageAgentTrace {
	routingDecision?: RoutingDecision;
	retrievalResults?: RetrievalResults;
	validationResults?: ValidationResults;
	webSearchResults?: WebSearchResults;
	agentTimeline: AgentActivity[];
}

export interface ClusterContext {
	broker_count?: number;
	brokers?: Record<string, unknown> | number;
	topic_count?: number;
	topics?: string[];
	consumer_groups?: Array<{ group_id: string; state?: string }> | string[];
	cluster_id?: string;
	controller_id?: number;
}

export interface ChatMessage extends Message {
	id: string;
	/** Unified sources - combines RAG docs, web results, etc. */
	citations?: Citation[];
	actions?: SuggestedAction[];
	operationResult?: ClusterOperationResult;
	adminResult?: AdminOperationResult;
	clusterContext?: ClusterContext;
	isStreaming?: boolean;
	isThinking?: boolean;
	thinkingStage?: string;
	/** Agent activity trace for educational visibility */
	agentTrace?: MessageAgentTrace;
}

// Current session store
export const currentSessionId = writable<string | null>(null);
export const currentSession = writable<ChatSession | null>(null);

// Sessions list store
export const sessions = writable<ChatSession[]>([]);
export const sessionsLoading = writable(false);

// Messages for current session
export const chatMessages = writable<ChatMessage[]>([]);
export const isProcessing = writable(false);

// Agent activity sidebar visibility
export const showAgentActivity = writable(false);

// Selected message ID for viewing its trace (null = show current/streaming trace)
export const selectedMessageId = writable<string | null>(null);

// Current agent activity (for the active message being streamed)
export const currentAgentTrace = writable<MessageAgentTrace>({
	agentTimeline: []
});

// Derived store: the trace to display in sidebar (selected message's trace or current streaming trace)
export const displayedAgentTrace = derived(
	[selectedMessageId, chatMessages, currentAgentTrace],
	([$selectedMessageId, $chatMessages, $currentAgentTrace]) => {
		if ($selectedMessageId) {
			// Find the selected message and return its stored trace
			const message = $chatMessages.find((m) => m.id === $selectedMessageId);
			if (message?.agentTrace) {
				return message.agentTrace;
			}
		}
		// Fall back to current streaming trace
		return $currentAgentTrace;
	}
);

// Derived store for chat history (for API calls)
export const chatHistory = derived(chatMessages, ($messages) =>
	$messages
		.filter((m) => !m.isStreaming)
		.map((m) => ({ role: m.role, content: m.content }))
);

// Session management functions
export async function loadSessions(): Promise<void> {
	sessionsLoading.set(true);
	try {
		const sessionsList = await getChatSessions();
		sessions.set(sessionsList);
	} catch (error) {
		console.error('Failed to load sessions:', error);
		sessions.set([]);
	} finally {
		sessionsLoading.set(false);
	}
}

export async function startNewSession(title: string = 'New Chat'): Promise<string> {
	try {
		const session = await createChatSession(title);
		sessions.update((s) => [session, ...s]);
		currentSessionId.set(session.id);
		currentSession.set(session);
		chatMessages.set([]);
		return session.id;
	} catch (error) {
		console.error('Failed to create session:', error);
		throw error;
	}
}

export async function loadSession(sessionId: string): Promise<void> {
	try {
		const data = await getChatSession(sessionId);
		currentSessionId.set(sessionId);
		currentSession.set(data.session);

		// Convert session messages to ChatMessage format, restoring agent traces
		const messages: ChatMessage[] = data.messages.map((m: ChatSessionMessage) => {
			// Convert stored agent_trace format to MessageAgentTrace format
			let agentTrace: MessageAgentTrace | undefined;
			if (m.agent_trace) {
				agentTrace = {
					routingDecision: m.agent_trace.routing_decision as RoutingDecision | undefined,
					retrievalResults: m.agent_trace.retrieval_results as RetrievalResults | undefined,
					validationResults: m.agent_trace.validation_results as ValidationResults | undefined,
					webSearchResults: m.agent_trace.web_search_results as WebSearchResults | undefined,
					agentTimeline: (m.agent_trace.agent_timeline || []).map((a) => ({
						agent: a.agent as AgentName,
						status: a.status as AgentStatus,
						description: a.description,
						duration_ms: a.duration_ms,
						result: a.result
					}))
				};
			}

			return {
				id: String(m.id),
				role: m.role as 'user' | 'assistant',
				content: m.content,
				citations: m.citations,
				actions: m.actions,
				agentTrace,
				isStreaming: false
			};
		});
		chatMessages.set(messages);

		// Clear any previous selection and reset current trace
		selectedMessageId.set(null);
		resetAgentTrace();
	} catch (error) {
		console.error('Failed to load session:', error);
		throw error;
	}
}

export async function removeSession(sessionId: string): Promise<void> {
	try {
		await deleteChatSession(sessionId);
		sessions.update((s) => s.filter((session) => session.id !== sessionId));

		// If we deleted the current session, clear it
		currentSessionId.update((id) => {
			if (id === sessionId) {
				currentSession.set(null);
				chatMessages.set([]);
				return null;
			}
			return id;
		});
	} catch (error) {
		console.error('Failed to delete session:', error);
		throw error;
	}
}

export async function renameSession(sessionId: string, title: string): Promise<void> {
	try {
		const updated = await updateChatSession(sessionId, title);
		sessions.update((s) => s.map((session) => (session.id === sessionId ? updated : session)));

		currentSession.update((s) => (s?.id === sessionId ? updated : s));
	} catch (error) {
		console.error('Failed to rename session:', error);
		throw error;
	}
}

export async function clearAllSessions(): Promise<void> {
	try {
		await clearAllChatSessions();
		sessions.set([]);
		currentSessionId.set(null);
		currentSession.set(null);
		chatMessages.set([]);
	} catch (error) {
		console.error('Failed to clear sessions:', error);
		throw error;
	}
}

// Message management functions (for local state during streaming)
export function addMessage(message: Omit<ChatMessage, 'id'>): string {
	const id = crypto.randomUUID();
	chatMessages.update((messages) => [...messages, { ...message, id }]);
	return id;
}

/**
 * Safely extract string content from various input types.
 * Prevents [object Object] from appearing in messages.
 */
function safeStringContent(value: unknown): string {
	if (value === undefined || value === null) {
		return '';
	}
	if (typeof value === 'string') {
		return value;
	}
	if (typeof value === 'number') {
		return String(value);
	}
	if (Array.isArray(value)) {
		// Handle content block arrays like [{"type": "text", "text": "..."}]
		const texts = value
			.map((item) => {
				if (typeof item === 'string') return item;
				if (typeof item === 'object' && item !== null) {
					if ('text' in item && typeof item.text === 'string') return item.text;
					if ('content' in item && typeof item.content === 'string') return item.content;
				}
				return '';
			})
			.filter(Boolean);
		return texts.join('');
	}
	if (typeof value === 'object') {
		// Handle object formats with text or content properties
		const obj = value as Record<string, unknown>;
		if ('text' in obj && typeof obj.text === 'string') return obj.text;
		if ('content' in obj && typeof obj.content === 'string') return obj.content;
		// Log unexpected object to help debug
		console.warn('[kGPT] Unexpected object in content, ignoring:', value);
		return '';
	}
	// Log unexpected type
	console.warn('[kGPT] Unexpected content type:', typeof value, value);
	return '';
}

export function updateMessage(id: string, updates: Partial<ChatMessage>): void {
	// Ensure content is a string if being updated - prevent [object Object]
	const safeUpdates = updates.content !== undefined
		? { ...updates, content: safeStringContent(updates.content) }
		: updates;
	chatMessages.update((messages) =>
		messages.map((msg) => (msg.id === id ? { ...msg, ...safeUpdates } : msg))
	);
}

export function appendToMessage(id: string, content: unknown): void {
	// Ensure content is a string to prevent [object Object]
	const safeContent = safeStringContent(content);
	if (!safeContent) return; // Don't append empty strings
	chatMessages.update((messages) =>
		messages.map((msg) => (msg.id === id ? { ...msg, content: (msg.content ?? '') + safeContent } : msg))
	);
}

export function setThinkingStage(id: string, stage: string): void {
	chatMessages.update((messages) =>
		messages.map((msg) => (msg.id === id ? { ...msg, thinkingStage: stage, isThinking: true } : msg))
	);
}

export function clearMessages(): void {
	chatMessages.set([]);
	currentSessionId.set(null);
	currentSession.set(null);
	selectedMessageId.set(null);
	resetAgentTrace();
}

/**
 * Select a message to view its agent trace in the sidebar.
 * Pass null to deselect and show the current/streaming trace.
 */
export function selectMessageForTrace(messageId: string | null): void {
	selectedMessageId.set(messageId);
	// Auto-open the sidebar when selecting a message
	if (messageId) {
		showAgentActivity.set(true);
	}
}

// ============================================================================
// Agent Activity Functions
// ============================================================================

export function resetAgentTrace(): void {
	currentAgentTrace.set({
		agentTimeline: []
	});
}

export function handleAgentEvent(event: AgentEvent): void {
	currentAgentTrace.update((trace) => {
		const timeline = [...trace.agentTimeline];
		const existingIndex = timeline.findIndex((a) => a.agent === event.agent);

		if (event.status === 'started') {
			if (existingIndex === -1) {
				timeline.push({
					agent: event.agent,
					status: 'started',
					description: event.description,
					startTime: Date.now()
				});
			} else {
				timeline[existingIndex] = {
					...timeline[existingIndex],
					status: 'started',
					description: event.description,
					startTime: Date.now()
				};
			}
		} else if (event.status === 'completed' || event.status === 'error') {
			if (existingIndex !== -1) {
				timeline[existingIndex] = {
					...timeline[existingIndex],
					status: event.status,
					endTime: Date.now(),
					duration_ms: event.duration_ms,
					result: event.result
				};
			} else {
				timeline.push({
					agent: event.agent,
					status: event.status,
					endTime: Date.now(),
					duration_ms: event.duration_ms,
					result: event.result
				});
			}
		}

		return { ...trace, agentTimeline: timeline };
	});
}

export function handleRoutingDecision(decision: RoutingDecision): void {
	currentAgentTrace.update((trace) => ({
		...trace,
		routingDecision: decision
	}));
}

export function handleRetrievalResults(results: RetrievalResults): void {
	currentAgentTrace.update((trace) => ({
		...trace,
		retrievalResults: results
	}));
}

export function handleValidationResults(results: ValidationResults): void {
	currentAgentTrace.update((trace) => ({
		...trace,
		validationResults: results
	}));
}

export function handleWebSearchResults(results: WebSearchResults): void {
	currentAgentTrace.update((trace) => ({
		...trace,
		webSearchResults: results
	}));
}

export function finalizeAgentTrace(messageId: string): void {
	// Copy the current trace to the message (but don't reset - keep visible in sidebar)
	currentAgentTrace.subscribe((trace) => {
		if (trace.agentTimeline.length > 0) {
			updateMessage(messageId, { agentTrace: { ...trace } });
		}
	})();
	// Note: We intentionally don't reset the trace here so it stays visible in the sidebar
	// The trace is reset when a new message starts streaming (in resetAgentTrace call at start of sendMessage)
}

export function toggleAgentActivity(): void {
	showAgentActivity.update((v) => !v);
}
