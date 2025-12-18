import { writable, derived } from 'svelte/store';
import type { Message, ChatSession, ChatSessionMessage, SuggestedAction, ClusterOperationResult } from '$lib/api';
import {
	getChatSessions,
	createChatSession,
	getChatSession,
	deleteChatSession,
	updateChatSession,
	clearAllChatSessions
} from '$lib/api';

export interface ChatMessage extends Message {
	id: string;
	citations?: string[];
	actions?: SuggestedAction[];
	operationResult?: ClusterOperationResult;
	clusterContext?: {
		broker_count?: number;
		brokers?: Record<string, unknown> | number;
		topic_count?: number;
		topics?: string[];
		consumer_groups?: string[];
		cluster_id?: string;
	};
	isStreaming?: boolean;
	isThinking?: boolean;
	thinkingStage?: string;
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

		// Convert session messages to ChatMessage format
		const messages: ChatMessage[] = data.messages.map((m: ChatSessionMessage) => ({
			id: String(m.id),
			role: m.role as 'user' | 'assistant',
			content: m.content,
			citations: m.citations,
			actions: m.actions,
			isStreaming: false
		}));
		chatMessages.set(messages);
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

export function updateMessage(id: string, updates: Partial<ChatMessage>): void {
	chatMessages.update((messages) =>
		messages.map((msg) => (msg.id === id ? { ...msg, ...updates } : msg))
	);
}

export function appendToMessage(id: string, content: string): void {
	chatMessages.update((messages) =>
		messages.map((msg) => (msg.id === id ? { ...msg, content: msg.content + content } : msg))
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
}
