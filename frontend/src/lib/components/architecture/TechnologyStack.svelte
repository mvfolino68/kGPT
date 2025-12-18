<script lang="ts">
	const aiMlTools = [
		{ name: 'OpenAI', description: 'GPT-4o for chat & embeddings', color: 'emerald', letter: 'AI' },
		{ name: 'Cohere', description: 'Reranking for precision', color: 'orange', letter: 'C' },
		{ name: 'Exa', description: 'Neural web search', color: 'blue', letter: 'E' },
		{ name: 'LangGraph', description: 'Agent orchestration', color: 'violet', icon: 'M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101' }
	];

	const dataTools = [
		{ name: 'Qdrant', description: 'Vector database', color: 'red', letter: 'Q' },
		{ name: 'Kafka', description: 'Cluster management', color: 'cyan', icon: 'M12 12m-2 0a2 2 0 1 0 4 0a2 2 0 1 0-4 0' },
		{ name: 'SQLite', description: 'Local persistence', color: 'amber', icon: 'M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4' },
		{ name: 'SSE', description: 'Real-time streaming', color: 'sky', icon: 'M5 12h14M12 5l7 7-7 7' }
	];

	const frameworks = [
		{ name: 'FastAPI', description: 'Python backend', color: 'teal', icon: 'M13 10V3L4 14h7v7l9-11h-7z' },
		{ name: 'SvelteKit', description: 'Frontend framework', color: 'orange', icon: 'M12 2c-5.523 0-10 4.477-10 10s4.477 10 10 10 10-4.477 10-10-4.477-10-10-10z' },
		{ name: 'LangChain', description: 'LLM abstractions', color: 'emerald', letter: 'LC' },
		{ name: 'Tailwind', description: 'Styling system', color: 'blue', icon: 'M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01' }
	];
</script>

<div class="bg-surface-900 border border-surface-700/50 rounded-lg overflow-hidden">
	<div class="px-6 py-4 border-b border-surface-700/50">
		<h2 class="text-sm text-surface-200">Technology Stack</h2>
		<p class="text-xs text-surface-500 mt-1">The services and tools powering kGPT</p>
	</div>

	<div class="p-6 space-y-6">
		<!-- AI & ML -->
		<div>
			<h3 class="text-[10px] font-bold text-surface-500 uppercase tracking-wider mb-3">
				AI & Machine Learning
			</h3>
			<div class="grid grid-cols-2 md:grid-cols-4 gap-3">
				{#each aiMlTools as tool}
					<div class="p-3 bg-surface-800/50 rounded-lg border border-surface-700/50 hover:border-{tool.color}-500/50 transition-colors">
						<div class="flex items-center gap-2 mb-2">
							<div class="w-8 h-8 rounded-lg bg-{tool.color}-500/10 flex items-center justify-center">
								{#if tool.icon}
									<svg class="w-4 h-4 text-{tool.color}-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
										<path stroke-linecap="round" stroke-linejoin="round" d={tool.icon} />
									</svg>
								{:else}
									<span class="text-{tool.color}-400 font-bold text-sm">{tool.letter}</span>
								{/if}
							</div>
							<span class="text-sm text-{tool.color}-400">{tool.name}</span>
						</div>
						<p class="text-xs text-surface-400">{tool.description}</p>
					</div>
				{/each}
			</div>
		</div>

		<!-- Data & Infrastructure -->
		<div>
			<h3 class="text-[10px] font-bold text-surface-500 uppercase tracking-wider mb-3">
				Data & Infrastructure
			</h3>
			<div class="grid grid-cols-2 md:grid-cols-4 gap-3">
				{#each dataTools as tool}
					<div class="p-3 bg-surface-800/50 rounded-lg border border-surface-700/50 hover:border-{tool.color}-500/50 transition-colors">
						<div class="flex items-center gap-2 mb-2">
							<div class="w-8 h-8 rounded-lg bg-{tool.color}-500/10 flex items-center justify-center">
								{#if tool.icon}
									<svg class="w-4 h-4 text-{tool.color}-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
										<path stroke-linecap="round" stroke-linejoin="round" d={tool.icon} />
									</svg>
								{:else}
									<span class="text-{tool.color}-400 font-bold text-sm">{tool.letter}</span>
								{/if}
							</div>
							<span class="text-sm text-{tool.color}-400">{tool.name}</span>
						</div>
						<p class="text-xs text-surface-400">{tool.description}</p>
					</div>
				{/each}
			</div>
		</div>

		<!-- Frameworks -->
		<div>
			<h3 class="text-[10px] font-bold text-surface-500 uppercase tracking-wider mb-3">
				Frameworks
			</h3>
			<div class="grid grid-cols-2 md:grid-cols-4 gap-3">
				{#each frameworks as tool}
					<div class="p-3 bg-surface-800/50 rounded-lg border border-surface-700/50 hover:border-{tool.color}-500/50 transition-colors">
						<div class="flex items-center gap-2 mb-2">
							<div class="w-8 h-8 rounded-lg bg-{tool.color}-500/10 flex items-center justify-center">
								{#if tool.icon}
									<svg class="w-4 h-4 text-{tool.color}-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
										<path stroke-linecap="round" stroke-linejoin="round" d={tool.icon} />
									</svg>
								{:else}
									<span class="text-{tool.color}-400 font-bold text-sm">{tool.letter}</span>
								{/if}
							</div>
							<span class="text-sm text-{tool.color}-400">{tool.name}</span>
						</div>
						<p class="text-xs text-surface-400">{tool.description}</p>
					</div>
				{/each}
			</div>
		</div>
	</div>
</div>
