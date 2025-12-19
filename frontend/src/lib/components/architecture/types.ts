export interface ExecutionPath {
	id: number;
	name: string;
	shortName: string;
	description: string;
	nodes: string[];
	parallelNodes: string[];
	example: string;
	color: string;
	hint: string;
}

export interface NodeInfo {
	role: string;
	details: string[];
}

export const executionPaths: ExecutionPath[] = [
	{
		id: 0,
		name: 'Documentation',
		shortName: 'Docs',
		description: 'Questions about Kafka concepts, configurations, or best practices',
		nodes: ['router', 'retrieval', 'synthesis'],
		parallelNodes: ['web_search'],
		example: '"What is consumer lag?"',
		color: 'blue',
		hint: 'Searches indexed docs + web (if enabled) in parallel'
	},
	{
		id: 1,
		name: 'Cluster + Docs',
		shortName: 'Both',
		description: 'Questions needing live cluster data AND documentation context',
		nodes: ['router', 'kafka', 'retrieval', 'synthesis'],
		parallelNodes: ['web_search'],
		example: '"Is my topic config correct?"',
		color: 'emerald',
		hint: 'Fetches cluster info, then searches docs + web in parallel'
	},
	{
		id: 2,
		name: 'Admin Operation',
		shortName: 'Admin',
		description: 'Commands to create, modify, or delete cluster resources',
		nodes: ['router', 'admin', 'synthesis'],
		parallelNodes: [],
		example: '"Create topic events"',
		color: 'amber',
		hint: 'Prepares operations with confirmation before executing'
	},
	{
		id: 3,
		name: 'Direct Response',
		shortName: 'Direct',
		description: 'Simple greetings or help requests',
		nodes: ['router', 'synthesis'],
		parallelNodes: [],
		example: '"Hi! What can you do?"',
		color: 'violet',
		hint: 'No retrieval needed - responds directly'
	}
];

export const nodeInfo: Record<string, NodeInfo> = {
	router: {
		role: 'Analyzes your question and picks the best path',
		details: [
			'Uses LLM to understand intent',
			'Checks if cluster is connected',
			'Determines if docs/cluster/admin needed'
		]
	},
	retrieval: {
		role: 'Searches documentation for relevant context',
		details: ['Query expansion with LLM', 'Hybrid search (dense + sparse)', 'Reranking for quality']
	},
	web_search: {
		role: 'Searches the web via Exa for real-time information',
		details: ['Neural web search', 'Current Kafka articles', 'Runs parallel with retrieval']
	},
	kafka: {
		role: 'Fetches live data from your connected cluster',
		details: ['Topic metadata & configs', 'Consumer group status', 'Partition & broker info']
	},
	admin: {
		role: 'Prepares cluster operations for your confirmation',
		details: ['Create/delete topics', 'Alter configurations', 'Manage consumer groups']
	},
	synthesis: {
		role: 'Generates the final answer using all gathered context',
		details: ['Context-aware generation', 'Cites sources', 'Streams response in real-time']
	}
};

export function getPathColor(colorName: string, type: 'bg' | 'border' | 'text' | 'glow'): string {
	const colors: Record<string, Record<string, string>> = {
		blue: {
			bg: 'bg-blue-500/20',
			border: 'border-blue-400',
			text: 'text-blue-400',
			glow: 'shadow-blue-500/30'
		},
		emerald: {
			bg: 'bg-emerald-500/20',
			border: 'border-emerald-400',
			text: 'text-emerald-400',
			glow: 'shadow-emerald-500/30'
		},
		amber: {
			bg: 'bg-amber-500/20',
			border: 'border-amber-400',
			text: 'text-amber-400',
			glow: 'shadow-amber-500/30'
		},
		violet: {
			bg: 'bg-violet-500/20',
			border: 'border-violet-400',
			text: 'text-violet-400',
			glow: 'shadow-violet-500/30'
		}
	};
	return colors[colorName]?.[type] || '';
}

/**
 * Tailwind-safe node color mapping (avoid dynamic class names from API payloads).
 */
export function getNodeColor(nodeName: string): string {
	const colors: Record<string, string> = {
		router: 'text-blue-400',
		retrieval: 'text-emerald-400',
		kafka: 'text-cyan-400',
		admin: 'text-amber-400',
		synthesis: 'text-violet-400',
		web_search: 'text-primary'
	};

	return colors[nodeName] || 'text-text-secondary';
}
