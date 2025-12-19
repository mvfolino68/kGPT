/**
 * Shared configuration and utilities for agent trace components
 */

export interface AgentConfigItem {
	label: string;
	icon: string;
	color: string;
	bg: string;
}

export const agentConfig: Record<string, AgentConfigItem> = {
	router: {
		label: 'Router',
		icon: 'M13 10V3L4 14h7v7l9-11h-7z',
		color: 'text-violet-400',
		bg: 'bg-violet-500/10'
	},
	retrieval: {
		label: 'Retrieval',
		icon: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z',
		color: 'text-blue-400',
		bg: 'bg-blue-500/10'
	},
	kafka: {
		label: 'Kafka',
		icon: 'M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2',
		color: 'text-blue-400',
		bg: 'bg-blue-500/10'
	},
	admin: {
		label: 'Admin',
		icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z',
		color: 'text-amber-400',
		bg: 'bg-amber-500/10'
	},
	web_search: {
		label: 'Web Search',
		icon: 'M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9',
		color: 'text-green-400',
		bg: 'bg-green-500/10'
	},
	validation: {
		label: 'Validation',
		icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
		color: 'text-cyan-400',
		bg: 'bg-cyan-500/10'
	},
	synthesis: {
		label: 'Synthesis',
		icon: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z',
		color: 'text-cyan-400',
		bg: 'bg-cyan-500/10'
	},
	error: {
		label: 'Error',
		icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
		color: 'text-red-400',
		bg: 'bg-red-500/10'
	}
};

export function getStatusColor(status: string): string {
	switch (status) {
		case 'started':
			return 'bg-amber-500';
		case 'completed':
			return 'bg-emerald-500';
		case 'error':
			return 'bg-red-500';
		default:
			return 'bg-surface-600';
	}
}

export function formatDuration(ms: number | undefined): string {
	if (!ms) return '';
	if (ms < 1000) return `${ms}ms`;
	return `${(ms / 1000).toFixed(1)}s`;
}
