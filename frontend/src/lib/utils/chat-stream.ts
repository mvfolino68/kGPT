import { extractTextContent } from './text-extraction';

export interface StreamEvent {
	stage?: string;
	agent_event?: any;
	routing_decision?: any;
	retrieval_results?: any;
	validation_results?: any;
	web_results?: any;
	cluster_context?: any;
	admin_result?: any;
	citations?: string[];
	actions?: Array<{ label: string; value: string }>;
	session_title_update?: string;
	choices?: Array<{ delta?: { content?: unknown } }>;
}

/**
 * Process SSE stream and update messages.
 * Uses non-blocking reads with proper cleanup.
 */
export async function* processSSEStream(
	response: Response,
	onStageUpdate?: (stage: string) => void,
	onAgentEvent?: (event: any) => void,
	onRoutingDecision?: (decision: any) => void,
	onRetrievalResults?: (results: any) => void,
	onValidationResults?: (results: any) => void,
	onWebResults?: (results: any) => void,
	onClusterContext?: (context: any) => void,
	onAdminResult?: (result: any) => void,
	onSessionTitleUpdate?: (title: string) => void
): AsyncGenerator<{ type: 'content' | 'citations' | 'actions'; data: any }, void, unknown> {
	if (!response.body) throw new Error('No response body');

	const reader = response.body.getReader();
	const decoder = new TextDecoder();
	let buffer = '';

	try {
		while (true) {
			// Read with a timeout to prevent hanging
			const readPromise = reader.read();

			// Use a 60-second timeout for each read operation
			const timeoutPromise = new Promise<{ done: true; value: undefined }>((_, reject) => {
				setTimeout(() => reject(new Error('Stream read timeout')), 60000);
			});

			let result: ReadableStreamReadResult<Uint8Array>;
			try {
				result = await Promise.race([readPromise, timeoutPromise]);
			} catch (error) {
				// Timeout or other error - break the loop
				console.warn('[kGPT] Stream read error:', error);
				break;
			}

			const { done, value } = result;
			if (done) {
				break;
			}

			buffer += decoder.decode(value, { stream: true });
			const lines = buffer.split('\n');
			buffer = lines.pop() || '';

			let streamComplete = false;

			for (const line of lines) {
				if (!line.startsWith('data: ')) continue;
				const data = line.slice(6);
				if (data === '[DONE]') {
					streamComplete = true;
					break;
				}

				try {
					const parsed: StreamEvent = JSON.parse(data);

					// Handle stage updates
					if (parsed.stage !== undefined) {
						onStageUpdate?.(parsed.stage);
						continue;
					}

					// Handle agent events
					if (parsed.agent_event) {
						onAgentEvent?.(parsed.agent_event);
						continue;
					}

					// Handle routing decision
					if (parsed.routing_decision) {
						onRoutingDecision?.(parsed.routing_decision);
						continue;
					}

					// Handle retrieval results
					if (parsed.retrieval_results) {
						onRetrievalResults?.(parsed.retrieval_results);
						continue;
					}

					// Handle validation results
					if (parsed.validation_results) {
						onValidationResults?.(parsed.validation_results);
						continue;
					}

					// Handle web search results
					if (parsed.web_results) {
						onWebResults?.(parsed.web_results);
						continue;
					}

					// Handle cluster context
					if (parsed.cluster_context) {
						onClusterContext?.(parsed.cluster_context);
						continue;
					}

					// Handle admin result
					if (parsed.admin_result) {
						onAdminResult?.(parsed.admin_result);
						continue;
					}

					// Handle session title update
					if (parsed.session_title_update) {
						onSessionTitleUpdate?.(parsed.session_title_update);
						continue;
					}

					// Handle actions
					if (parsed.actions) {
						yield { type: 'actions', data: parsed.actions };
						continue;
					}

					// Handle citations
					if (parsed.citations) {
						yield { type: 'citations', data: parsed.citations };
						continue;
					}

					// Handle content chunks
					const rawContent = parsed.choices?.[0]?.delta?.content;
					if (rawContent !== undefined && rawContent !== null) {
						const textContent = extractTextContent(rawContent);
						if (textContent) {
							yield { type: 'content', data: textContent };
						}
					}
				} catch {
					// Skip malformed JSON
				}
			}

			if (streamComplete) break;
		}
	} finally {
		// Always release the reader lock
		try {
			reader.releaseLock();
		} catch {
			// Ignore errors during cleanup
		}
	}
}

/**
 * Create a fetch request with an AbortController for streaming.
 * Returns both the response and the abort controller.
 */
export async function fetchWithAbort(
	url: string,
	options: RequestInit,
	timeoutMs: number = 120000
): Promise<{ response: Response; abort: () => void }> {
	const controller = new AbortController();

	// Set overall request timeout
	const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

	try {
		const response = await fetch(url, {
			...options,
			signal: controller.signal,
		});

		return {
			response,
			abort: () => {
				clearTimeout(timeoutId);
				controller.abort();
			},
		};
	} catch (error) {
		clearTimeout(timeoutId);
		throw error;
	}
}
