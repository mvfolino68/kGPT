<script lang="ts">
	import { onMount } from 'svelte';
	import { getAgentGraph, type AgentGraphInfo, type AgentGraphNode } from '$lib/api';
	import { RetroHeader, RetroCard, RetroButton, StatusIndicator } from '$lib/components';

	let agentGraph = $state<AgentGraphInfo | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);
	let selectedPath = $state<number>(0);
	let selectedNode = $state<string | null>(null);

	onMount(async () => {
		await loadGraph();
	});

	async function loadGraph() {
		loading = true;
		error = null;
		try {
			agentGraph = await getAgentGraph();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load agent graph';
		} finally {
			loading = false;
		}
	}

	function getNodeById(name: string): AgentGraphNode | undefined {
		return agentGraph?.nodes.find((n) => n.name === name);
	}

	// Execution paths - the 4 main flows through the system
	// Note: web_search runs in parallel with retrieval when enabled
	const executionPaths = [
		{
			id: 0,
			name: 'Documentation',
			shortName: 'Docs',
			description: 'Questions about Kafka concepts, configurations, or best practices',
			nodes: ['router', 'retrieval', 'synthesis'],
			parallelNodes: ['web_search'], // Can run in parallel with retrieval
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
			parallelNodes: ['web_search'], // Can run in parallel with retrieval
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

	// Check if a node is in the currently selected path
	function isNodeActive(nodeName: string): boolean {
		return executionPaths[selectedPath].nodes.includes(nodeName);
	}

	// Get the position of a node in the current path (for animation delay)
	function getNodePosition(nodeName: string): number {
		return executionPaths[selectedPath].nodes.indexOf(nodeName);
	}

	// Color utilities
	function getPathColor(colorName: string, type: 'bg' | 'border' | 'text' | 'glow'): string {
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

	// Node metadata for display
	const nodeInfo: Record<string, { role: string; details: string[] }> = {
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
			details: [
				'Create/delete topics',
				'Alter configurations',
				'Manage consumer groups'
			]
		},
		synthesis: {
			role: 'Generates the final answer using all gathered context',
			details: ['Context-aware generation', 'Cites sources', 'Streams response in real-time']
		}
	};
</script>

<svelte:head>
	<title>kGPT - Architecture</title>
</svelte:head>

<div class="flex flex-col h-full bg-surface-950">
	<RetroHeader path="kgpt/architecture" flag="--agent-graph">
		{#snippet rightContent()}
			<div class="flex items-center gap-4 text-xs font-mono">
				<div class="flex items-center gap-2">
					<StatusIndicator status="active" size="sm" pulse />
					<span class="text-surface-400">LangGraph</span>
				</div>
				<RetroButton size="sm" onclick={loadGraph} disabled={loading}>
					{loading ? 'loading...' : 'refresh'}
				</RetroButton>
			</div>
		{/snippet}
	</RetroHeader>

	<div class="flex-1 overflow-y-auto p-6">
		<div class="max-w-5xl mx-auto space-y-8">
			{#if error}
				<RetroCard variant="error">
					<div class="flex items-center gap-3">
						<StatusIndicator status="error" />
						<span class="font-mono text-sm text-red-400">{error}</span>
						<RetroButton size="sm" onclick={loadGraph}>retry</RetroButton>
					</div>
				</RetroCard>
			{:else if loading}
				<div class="flex items-center justify-center py-20">
					<div class="text-center space-y-4">
						<div
							class="w-12 h-12 mx-auto border-2 border-blue-500 border-t-transparent rounded-full animate-spin"
						></div>
						<p class="font-mono text-surface-400">Loading agent graph...</p>
					</div>
				</div>
			{:else if agentGraph}
				<!-- Hero -->
				<section class="text-center py-6">
					<h1 class="text-3xl font-bold font-mono text-surface-100 mb-3">
						Multi-Agent Orchestration
					</h1>
					<p class="text-surface-400 font-mono text-sm max-w-2xl mx-auto">
						Your question flows through specialized AI agents. Select a path below to see how
						different queries are handled.
					</p>
				</section>

				<!-- Path Selector -->
				<div class="flex justify-center">
					<div class="inline-flex bg-surface-900 rounded-xl p-1.5 gap-1">
						{#each executionPaths as path}
							<button
								onclick={() => (selectedPath = path.id)}
								class="px-4 py-2.5 rounded-lg font-mono text-sm transition-all duration-200 {selectedPath ===
								path.id
									? `${getPathColor(path.color, 'bg')} ${getPathColor(path.color, 'text')} ${getPathColor(path.color, 'border')} border shadow-lg ${getPathColor(path.color, 'glow')}`
									: 'text-surface-400 hover:text-surface-200 hover:bg-surface-800 border border-transparent'}"
							>
								{path.shortName}
							</button>
						{/each}
					</div>
				</div>

				<!-- Selected Path Info -->
				<div
					class="text-center p-4 rounded-xl {getPathColor(executionPaths[selectedPath].color, 'bg')} border {getPathColor(executionPaths[selectedPath].color, 'border')}"
				>
					<h2
						class="font-mono text-lg font-bold {getPathColor(executionPaths[selectedPath].color, 'text')} mb-1"
					>
						{executionPaths[selectedPath].name}
					</h2>
					<p class="text-surface-300 text-sm">{executionPaths[selectedPath].description}</p>
					<p class="text-surface-500 text-xs mt-2 italic">
						{executionPaths[selectedPath].example}
					</p>
				</div>

				<!-- Interactive Graph -->
				<RetroCard noPadding>
					<div class="px-6 py-4 border-b retro-border">
						<div class="flex items-center justify-between">
							<div class="flex items-center gap-3">
								<div
									class="w-2 h-2 rounded-full {getPathColor(executionPaths[selectedPath].color, 'bg')} {getPathColor(executionPaths[selectedPath].color, 'border')} border animate-pulse"
								></div>
								<span class="font-mono text-sm text-surface-200">Query Flow</span>
							</div>
							<span class="text-xs text-surface-500 font-mono"
								>Click any agent for details</span
							>
						</div>
					</div>

					<div class="p-8">
						<!-- Vertical Flow -->
						<div class="flex flex-col items-center gap-2">
							<!-- START -->
							<div
								class="px-5 py-2 bg-surface-800 border border-surface-600 rounded-lg font-mono text-sm text-surface-400"
							>
								START
							</div>

							<!-- Arrow down -->
							<div class="flex flex-col items-center">
								<div class="w-0.5 h-6 bg-surface-600"></div>
								<svg
									class="w-3 h-3 text-surface-600 -mt-1"
									fill="currentColor"
									viewBox="0 0 12 12"
								>
									<path d="M6 9L1 4h10L6 9z" />
								</svg>
							</div>

							<!-- Agent Nodes -->
							{#each executionPaths[selectedPath].nodes as nodeName, index}
								{@const node = getNodeById(nodeName)}
								{@const info = nodeInfo[nodeName]}
								{@const isActive = isNodeActive(nodeName)}
								{@const pathColor = executionPaths[selectedPath].color}
								{@const hasParallel = nodeName === 'retrieval' && executionPaths[selectedPath].parallelNodes?.includes('web_search')}
								{@const webSearchInfo = nodeInfo['web_search']}

								{#if node}
									<!-- Check if this node runs in parallel with web_search -->
									{#if hasParallel}
										<!-- Parallel execution container -->
										<div class="w-full max-w-lg">
											<div class="flex items-center justify-center gap-2 mb-2">
												<div class="h-px flex-1 bg-surface-700"></div>
												<span class="text-xs font-mono text-surface-500 px-2">parallel</span>
												<div class="h-px flex-1 bg-surface-700"></div>
											</div>
											<div class="flex gap-3">
												<!-- Retrieval Node -->
												<button
													onclick={() => (selectedNode = selectedNode === nodeName ? null : nodeName)}
													class="flex-1 p-3 rounded-xl border-2 transition-all duration-300 {isActive
														? `${getPathColor(pathColor, 'bg')} ${getPathColor(pathColor, 'border')} shadow-lg ${getPathColor(pathColor, 'glow')}`
														: 'bg-surface-900 border-surface-700 opacity-40'}"
													style="animation-delay: {index * 100}ms"
												>
													<div class="flex items-center gap-3">
														<div
															class="w-10 h-10 rounded-lg flex items-center justify-center {isActive ? getPathColor(pathColor, 'bg') : 'bg-surface-800'}"
														>
															<svg
																class="w-5 h-5 {isActive ? getPathColor(pathColor, 'text') : 'text-surface-500'}"
																fill="none"
																stroke="currentColor"
																viewBox="0 0 24 24"
																stroke-width="2"
															>
																<path stroke-linecap="round" stroke-linejoin="round" d={node.icon} />
															</svg>
														</div>
														<div class="flex-1 text-left">
															<div class="font-mono text-sm font-bold {isActive ? getPathColor(pathColor, 'text') : 'text-surface-500'}">
																{node.label}
															</div>
															<div class="text-xs text-surface-400 mt-0.5">Searches indexed docs</div>
														</div>
													</div>
													{#if selectedNode === nodeName && info}
														<div class="mt-3 pt-3 border-t border-current/20">
															<div class="space-y-1">
																{#each info.details as detail}
																	<div class="text-xs text-left text-surface-300">* {detail}</div>
																{/each}
															</div>
														</div>
													{/if}
												</button>

												<!-- Web Search Node (Exa) -->
												<button
													onclick={() => (selectedNode = selectedNode === 'web_search' ? null : 'web_search')}
													class="flex-1 p-3 rounded-xl border-2 transition-all duration-300 {getPathColor(pathColor, 'bg')} {getPathColor(pathColor, 'border')} shadow-lg {getPathColor(pathColor, 'glow')}"
													style="animation-delay: {(index + 0.5) * 100}ms"
												>
													<div class="flex items-center gap-3">
														<div class="w-10 h-10 rounded-lg flex items-center justify-center {getPathColor(pathColor, 'bg')}">
															<svg
																class="w-5 h-5 {getPathColor(pathColor, 'text')}"
																fill="none"
																stroke="currentColor"
																viewBox="0 0 24 24"
																stroke-width="2"
															>
																<path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
															</svg>
														</div>
														<div class="flex-1 text-left">
															<div class="font-mono text-sm font-bold {getPathColor(pathColor, 'text')}">
																Exa Search
															</div>
															<div class="text-xs text-surface-400 mt-0.5">Real-time web search</div>
														</div>
													</div>
													{#if selectedNode === 'web_search' && webSearchInfo}
														<div class="mt-3 pt-3 border-t border-current/20">
															<div class="space-y-1">
																{#each webSearchInfo.details as detail}
																	<div class="text-xs text-left text-surface-300">* {detail}</div>
																{/each}
															</div>
														</div>
													{/if}
												</button>
											</div>
											<div class="flex items-center justify-center gap-2 mt-2">
												<div class="h-px flex-1 bg-surface-700"></div>
												<span class="text-xs font-mono text-surface-500 px-2">merge</span>
												<div class="h-px flex-1 bg-surface-700"></div>
											</div>
										</div>
									{:else}
										<!-- Regular single node -->
										<button
											onclick={() => (selectedNode = selectedNode === nodeName ? null : nodeName)}
											class="w-full max-w-md p-4 rounded-xl border-2 transition-all duration-300 {isActive
												? `${getPathColor(pathColor, 'bg')} ${getPathColor(pathColor, 'border')} shadow-lg ${getPathColor(pathColor, 'glow')}`
												: 'bg-surface-900 border-surface-700 opacity-40'}"
											style="animation-delay: {index * 100}ms"
										>
											<div class="flex items-center gap-4">
												<!-- Icon -->
												<div
													class="w-12 h-12 rounded-xl flex items-center justify-center {isActive ? getPathColor(pathColor, 'bg') : 'bg-surface-800'}"
												>
													<svg
														class="w-6 h-6 {isActive ? getPathColor(pathColor, 'text') : 'text-surface-500'}"
														fill="none"
														stroke="currentColor"
														viewBox="0 0 24 24"
														stroke-width="2"
													>
														<path
															stroke-linecap="round"
															stroke-linejoin="round"
															d={node.icon}
														/>
													</svg>
												</div>

												<!-- Info -->
												<div class="flex-1 text-left">
													<div
														class="font-mono text-sm font-bold {isActive ? getPathColor(pathColor, 'text') : 'text-surface-500'}"
													>
														{node.label}
													</div>
													<div class="text-xs text-surface-400 mt-0.5">
														{info?.role || node.description}
													</div>
												</div>

												<!-- Step number -->
												<div
													class="w-8 h-8 rounded-full flex items-center justify-center font-mono text-sm {isActive ? `${getPathColor(pathColor, 'bg')} ${getPathColor(pathColor, 'text')}` : 'bg-surface-800 text-surface-500'}"
												>
													{index + 1}
												</div>
											</div>

											<!-- Expanded details -->
											{#if selectedNode === nodeName && info}
												<div
													class="mt-4 pt-4 border-t {isActive ? 'border-current/20' : 'border-surface-700'}"
												>
													<div class="grid grid-cols-3 gap-2">
														{#each info.details as detail}
															<div
																class="text-xs text-left p-2 rounded-lg {isActive ? 'bg-surface-900/50' : 'bg-surface-800'}"
															>
																<span
																	class="{isActive ? getPathColor(pathColor, 'text') : 'text-surface-500'}"
																	>*</span
																>
																<span class="text-surface-300 ml-1">{detail}</span>
															</div>
														{/each}
													</div>
												</div>
											{/if}
										</button>
									{/if}

									<!-- Arrow between nodes (not after last) -->
									{#if index < executionPaths[selectedPath].nodes.length - 1}
										<div class="flex flex-col items-center">
											<div
												class="w-0.5 h-6 {isActive ? getPathColor(pathColor, 'bg') : 'bg-surface-700'}"
											></div>
											<svg
												class="w-3 h-3 -mt-1 {isActive ? getPathColor(pathColor, 'text') : 'text-surface-700'}"
												fill="currentColor"
												viewBox="0 0 12 12"
											>
												<path d="M6 9L1 4h10L6 9z" />
											</svg>
										</div>
									{/if}
								{/if}
							{/each}

							<!-- Arrow to END -->
							<div class="flex flex-col items-center">
								<div
									class="w-0.5 h-6 {getPathColor(executionPaths[selectedPath].color, 'bg')}"
								></div>
								<svg
									class="w-3 h-3 -mt-1 {getPathColor(executionPaths[selectedPath].color, 'text')}"
									fill="currentColor"
									viewBox="0 0 12 12"
								>
									<path d="M6 9L1 4h10L6 9z" />
								</svg>
							</div>

							<!-- END -->
							<div
								class="px-5 py-2 rounded-lg font-mono text-sm {getPathColor(executionPaths[selectedPath].color, 'bg')} {getPathColor(executionPaths[selectedPath].color, 'text')} border {getPathColor(executionPaths[selectedPath].color, 'border')}"
							>
								END
							</div>
						</div>

						<!-- Hint -->
						<div class="mt-8 text-center">
							<p class="text-xs text-surface-500 font-mono">
								{executionPaths[selectedPath].hint}
							</p>
						</div>
					</div>
				</RetroCard>

				<!-- All Agents Overview -->
				<RetroCard noPadding>
					<div class="px-6 py-4 border-b retro-border">
						<h2 class="font-mono text-sm text-surface-200">All Agents</h2>
						<p class="text-xs text-surface-500 mt-1">
							The 6 specialized agents that power kGPT
						</p>
					</div>

					<div class="p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
						{#each agentGraph.nodes as node}
							{@const info = nodeInfo[node.name]}
							<div
								class="p-4 bg-surface-900/50 rounded-xl border border-surface-700 hover:border-surface-600 transition-colors"
							>
								<div class="flex items-center gap-3 mb-3">
									<div
										class="w-10 h-10 rounded-lg bg-surface-800 flex items-center justify-center"
									>
										<svg
											class="w-5 h-5 {node.color}"
											fill="none"
											stroke="currentColor"
											viewBox="0 0 24 24"
											stroke-width="2"
										>
											<path stroke-linecap="round" stroke-linejoin="round" d={node.icon} />
										</svg>
									</div>
									<div>
										<div class="font-mono text-sm font-bold {node.color}">{node.label}</div>
										<div class="text-xs text-surface-500">{node.name}</div>
									</div>
								</div>
								<p class="text-xs text-surface-400">{info?.role || node.description}</p>
							</div>
						{/each}
						<!-- Web Search Agent (Exa) - runs parallel with retrieval -->
						<div
							class="p-4 bg-surface-900/50 rounded-xl border border-surface-700 hover:border-blue-500/50 transition-colors"
						>
							<div class="flex items-center gap-3 mb-3">
								<div
									class="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center"
								>
									<svg
										class="w-5 h-5 text-blue-400"
										fill="none"
										stroke="currentColor"
										viewBox="0 0 24 24"
										stroke-width="2"
									>
										<path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
									</svg>
								</div>
								<div>
									<div class="font-mono text-sm font-bold text-blue-400">Exa Search</div>
									<div class="text-xs text-surface-500">web_search</div>
								</div>
							</div>
							<p class="text-xs text-surface-400">{nodeInfo['web_search']?.role || 'Real-time web search via Exa API'}</p>
						</div>
					</div>
				</RetroCard>

				<!-- Technology Stack -->
				<RetroCard noPadding>
					<div class="px-6 py-4 border-b retro-border">
						<h2 class="font-mono text-sm text-surface-200">Technology Stack</h2>
						<p class="text-xs text-surface-500 mt-1">
							The services and tools powering kGPT
						</p>
					</div>

					<div class="p-6">
						<!-- AI & ML -->
						<div class="mb-6">
							<h3 class="text-xs font-mono text-surface-500 uppercase tracking-wider mb-3">
								AI & Machine Learning
							</h3>
							<div class="grid grid-cols-2 md:grid-cols-4 gap-3">
								<div
									class="p-3 bg-surface-900/50 rounded-lg border border-surface-700 hover:border-emerald-500/50 transition-colors group"
								>
									<div class="flex items-center gap-2 mb-2">
										<div
											class="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center"
										>
											<span class="text-emerald-400 font-bold text-sm">AI</span>
										</div>
										<span class="font-mono text-sm text-emerald-400">OpenAI</span>
									</div>
									<p class="text-xs text-surface-400">GPT-4o for chat & embeddings</p>
								</div>

								<div
									class="p-3 bg-surface-900/50 rounded-lg border border-surface-700 hover:border-orange-500/50 transition-colors group"
								>
									<div class="flex items-center gap-2 mb-2">
										<div
											class="w-8 h-8 rounded-lg bg-orange-500/10 flex items-center justify-center"
										>
											<span class="text-orange-400 font-bold text-sm">C</span>
										</div>
										<span class="font-mono text-sm text-orange-400">Cohere</span>
									</div>
									<p class="text-xs text-surface-400">Reranking for precision</p>
								</div>

								<div
									class="p-3 bg-surface-900/50 rounded-lg border border-surface-700 hover:border-blue-500/50 transition-colors group"
								>
									<div class="flex items-center gap-2 mb-2">
										<div
											class="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center"
										>
											<span class="text-blue-400 font-bold text-sm">E</span>
										</div>
										<span class="font-mono text-sm text-blue-400">Exa</span>
									</div>
									<p class="text-xs text-surface-400">Neural web search</p>
								</div>

								<div
									class="p-3 bg-surface-900/50 rounded-lg border border-surface-700 hover:border-violet-500/50 transition-colors group"
								>
									<div class="flex items-center gap-2 mb-2">
										<div
											class="w-8 h-8 rounded-lg bg-violet-500/10 flex items-center justify-center"
										>
											<svg
												class="w-4 h-4 text-violet-400"
												fill="none"
												stroke="currentColor"
												viewBox="0 0 24 24"
												stroke-width="2"
											>
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101"
												/>
											</svg>
										</div>
										<span class="font-mono text-sm text-violet-400">LangGraph</span>
									</div>
									<p class="text-xs text-surface-400">Agent orchestration</p>
								</div>
							</div>
						</div>

						<!-- Data & Infrastructure -->
						<div class="mb-6">
							<h3 class="text-xs font-mono text-surface-500 uppercase tracking-wider mb-3">
								Data & Infrastructure
							</h3>
							<div class="grid grid-cols-2 md:grid-cols-4 gap-3">
								<div
									class="p-3 bg-surface-900/50 rounded-lg border border-surface-700 hover:border-red-500/50 transition-colors group"
								>
									<div class="flex items-center gap-2 mb-2">
										<div
											class="w-8 h-8 rounded-lg bg-red-500/10 flex items-center justify-center"
										>
											<span class="text-red-400 font-bold text-sm">Q</span>
										</div>
										<span class="font-mono text-sm text-red-400">Qdrant</span>
									</div>
									<p class="text-xs text-surface-400">Vector database</p>
								</div>

								<div
									class="p-3 bg-surface-900/50 rounded-lg border border-surface-700 hover:border-cyan-500/50 transition-colors group"
								>
									<div class="flex items-center gap-2 mb-2">
										<div
											class="w-8 h-8 rounded-lg bg-cyan-500/10 flex items-center justify-center"
										>
											<svg
												class="w-4 h-4 text-cyan-400"
												fill="none"
												stroke="currentColor"
												viewBox="0 0 24 24"
												stroke-width="2"
											>
												<circle cx="12" cy="12" r="2" />
												<circle cx="12" cy="5" r="1.5" />
												<circle cx="6" cy="17" r="1.5" />
												<circle cx="18" cy="17" r="1.5" />
											</svg>
										</div>
										<span class="font-mono text-sm text-cyan-400">Kafka</span>
									</div>
									<p class="text-xs text-surface-400">Cluster management</p>
								</div>

								<div
									class="p-3 bg-surface-900/50 rounded-lg border border-surface-700 hover:border-amber-500/50 transition-colors group"
								>
									<div class="flex items-center gap-2 mb-2">
										<div
											class="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center"
										>
											<svg
												class="w-4 h-4 text-amber-400"
												fill="none"
												stroke="currentColor"
												viewBox="0 0 24 24"
												stroke-width="2"
											>
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"
												/>
											</svg>
										</div>
										<span class="font-mono text-sm text-amber-400">SQLite</span>
									</div>
									<p class="text-xs text-surface-400">Local persistence</p>
								</div>

								<div
									class="p-3 bg-surface-900/50 rounded-lg border border-surface-700 hover:border-sky-500/50 transition-colors group"
								>
									<div class="flex items-center gap-2 mb-2">
										<div
											class="w-8 h-8 rounded-lg bg-sky-500/10 flex items-center justify-center"
										>
											<svg
												class="w-4 h-4 text-sky-400"
												fill="none"
												stroke="currentColor"
												viewBox="0 0 24 24"
												stroke-width="2"
											>
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													d="M5 12h14M12 5l7 7-7 7"
												/>
											</svg>
										</div>
										<span class="font-mono text-sm text-sky-400">SSE</span>
									</div>
									<p class="text-xs text-surface-400">Real-time streaming</p>
								</div>
							</div>
						</div>

						<!-- Frameworks -->
						<div>
							<h3 class="text-xs font-mono text-surface-500 uppercase tracking-wider mb-3">
								Frameworks
							</h3>
							<div class="grid grid-cols-2 md:grid-cols-4 gap-3">
								<div
									class="p-3 bg-surface-900/50 rounded-lg border border-surface-700 hover:border-teal-500/50 transition-colors group"
								>
									<div class="flex items-center gap-2 mb-2">
										<div
											class="w-8 h-8 rounded-lg bg-teal-500/10 flex items-center justify-center"
										>
											<svg
												class="w-4 h-4 text-teal-400"
												fill="none"
												stroke="currentColor"
												viewBox="0 0 24 24"
												stroke-width="2"
											>
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													d="M13 10V3L4 14h7v7l9-11h-7z"
												/>
											</svg>
										</div>
										<span class="font-mono text-sm text-teal-400">FastAPI</span>
									</div>
									<p class="text-xs text-surface-400">Python backend</p>
								</div>

								<div
									class="p-3 bg-surface-900/50 rounded-lg border border-surface-700 hover:border-orange-500/50 transition-colors group"
								>
									<div class="flex items-center gap-2 mb-2">
										<div
											class="w-8 h-8 rounded-lg bg-orange-500/10 flex items-center justify-center"
										>
											<svg
												class="w-4 h-4 text-orange-400"
												fill="currentColor"
												viewBox="0 0 24 24"
											>
												<path
													d="M12.002 2c-5.522 0-9.998 4.476-9.998 9.998 0 5.523 4.476 9.998 9.998 9.998 5.523 0 9.998-4.475 9.998-9.998 0-5.522-4.475-9.998-9.998-9.998zm0 1.5a8.498 8.498 0 110 16.996 8.498 8.498 0 010-16.996z"
												/>
											</svg>
										</div>
										<span class="font-mono text-sm text-orange-400">SvelteKit</span>
									</div>
									<p class="text-xs text-surface-400">Frontend framework</p>
								</div>

								<div
									class="p-3 bg-surface-900/50 rounded-lg border border-surface-700 hover:border-emerald-500/50 transition-colors group"
								>
									<div class="flex items-center gap-2 mb-2">
										<div
											class="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center"
										>
											<span class="text-emerald-400 font-bold text-xs">LC</span>
										</div>
										<span class="font-mono text-sm text-emerald-400">LangChain</span>
									</div>
									<p class="text-xs text-surface-400">LLM abstractions</p>
								</div>

								<div
									class="p-3 bg-surface-900/50 rounded-lg border border-surface-700 hover:border-blue-500/50 transition-colors group"
								>
									<div class="flex items-center gap-2 mb-2">
										<div
											class="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center"
										>
											<svg
												class="w-4 h-4 text-blue-400"
												fill="none"
												stroke="currentColor"
												viewBox="0 0 24 24"
												stroke-width="2"
											>
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01"
												/>
											</svg>
										</div>
										<span class="font-mono text-sm text-blue-400">Tailwind</span>
									</div>
									<p class="text-xs text-surface-400">Styling system</p>
								</div>
							</div>
						</div>
					</div>

					<!-- Graph Stats -->
					<div class="px-6 py-4 border-t retro-border bg-surface-900/30">
						<div class="flex items-center justify-center gap-8 text-xs font-mono">
							<div class="text-center">
								<div class="text-blue-400 text-lg font-bold">{agentGraph.nodes.length + 1}</div>
								<div class="text-surface-500">Agents</div>
							</div>
							<div class="text-center">
								<div class="text-emerald-400 text-lg font-bold">{agentGraph.edges.length}</div>
								<div class="text-surface-500">Connections</div>
							</div>
							<div class="text-center">
								<div class="text-violet-400 text-lg font-bold">4</div>
								<div class="text-surface-500">Paths</div>
							</div>
							<div class="text-center">
								<div class="text-amber-400 text-lg font-bold">12+</div>
								<div class="text-surface-500">Technologies</div>
							</div>
						</div>
					</div>
				</RetroCard>

				<!-- CTA -->
				<RetroCard variant="glow-blue" class="text-center">
					<div class="py-4">
						<h3 class="font-mono text-lg text-surface-100 mb-2">See It In Action</h3>
						<p class="text-sm text-surface-400 mb-4">
							Watch the agent pipeline process your queries in real-time with the Activity
							sidebar.
						</p>
						<a
							href="/"
							class="inline-flex items-center gap-2 px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white font-mono text-sm rounded-lg transition-colors"
						>
							<svg
								class="w-4 h-4"
								fill="none"
								stroke="currentColor"
								viewBox="0 0 24 24"
								stroke-width="2"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
								/>
							</svg>
							Start Chatting
						</a>
					</div>
				</RetroCard>
			{/if}
		</div>
	</div>
</div>
