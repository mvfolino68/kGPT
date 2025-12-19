<script lang="ts">
	import { Card } from '$lib/components';
	import OverviewTile from './OverviewTile.svelte';

	type TechColor =
		| 'emerald'
		| 'orange'
		| 'blue'
		| 'violet'
		| 'red'
		| 'cyan'
		| 'amber'
		| 'sky'
		| 'teal';

	type TechItem = {
		name: string;
		description: string;
		color: TechColor;
		icon?: string;
		letter?: string;
	};

	const colorClasses: Record<TechColor, { bg: string; text: string }> = {
		emerald: { bg: 'bg-emerald-500/10', text: 'text-emerald-400' },
		orange: { bg: 'bg-orange-500/10', text: 'text-orange-400' },
		blue: { bg: 'bg-blue-500/10', text: 'text-blue-400' },
		violet: { bg: 'bg-violet-500/10', text: 'text-violet-400' },
		red: { bg: 'bg-red-500/10', text: 'text-red-400' },
		cyan: { bg: 'bg-cyan-500/10', text: 'text-cyan-400' },
		amber: { bg: 'bg-amber-500/10', text: 'text-amber-400' },
		sky: { bg: 'bg-sky-500/10', text: 'text-sky-400' },
		teal: { bg: 'bg-teal-500/10', text: 'text-teal-400' }
	};

	const aiMlTools = [
		{ name: 'OpenAI', description: 'Chat + embeddings', color: 'emerald', letter: 'AI' },
		{ name: 'Cohere', description: 'Reranking for precision', color: 'orange', letter: 'C' },
		{ name: 'Exa', description: 'Neural web search', color: 'blue', letter: 'E' },
		{ name: 'LangGraph', description: 'Agent orchestration', color: 'violet', icon: 'M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101' }
	] satisfies TechItem[];

	const dataTools = [
		{ name: 'Qdrant', description: 'Vector database', color: 'red', letter: 'Q' },
		{ name: 'Kafka', description: 'Cluster management', color: 'cyan', icon: 'M12 12m-2 0a2 2 0 1 0 4 0a2 2 0 1 0-4 0' },
		{ name: 'SQLite', description: 'Local persistence', color: 'amber', icon: 'M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4' },
		{ name: 'SSE', description: 'Real-time streaming', color: 'sky', icon: 'M5 12h14M12 5l7 7-7 7' }
	] satisfies TechItem[];

	const frameworks = [
		{ name: 'FastAPI', description: 'Python backend', color: 'teal', icon: 'M13 10V3L4 14h7v7l9-11h-7z' },
		{ name: 'SvelteKit', description: 'Frontend framework', color: 'orange', icon: 'M12 2c-5.523 0-10 4.477-10 10s4.477 10 10 10 10-4.477 10-10-4.477-10-10-10z' },
		{ name: 'LangChain', description: 'LLM abstractions', color: 'emerald', letter: 'LC' },
		{ name: 'Tailwind', description: 'Styling system', color: 'blue', icon: 'M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01' }
	] satisfies TechItem[];
</script>

<Card
	title="Technology stack"
	subtitle="The services and tools powering kGPT"
>
	<div class="space-y-6">
		<!-- AI & ML -->
		<div>
			<h3 class="label mb-3">AI & machine learning</h3>
			<div class="grid grid-cols-2 md:grid-cols-4 gap-3">
				{#each aiMlTools as tool}
					{@const tone = colorClasses[tool.color]}
					<OverviewTile
						title={tool.name}
						description={tool.description}
						tone={tone}
						iconPath={tool.icon}
						letter={tool.letter}
					/>
				{/each}
			</div>
		</div>

		<!-- Data & Infrastructure -->
		<div>
			<h3 class="label mb-3">Data & infrastructure</h3>
			<div class="grid grid-cols-2 md:grid-cols-4 gap-3">
				{#each dataTools as tool}
					{@const tone = colorClasses[tool.color]}
					<OverviewTile
						title={tool.name}
						description={tool.description}
						tone={tone}
						iconPath={tool.icon}
						letter={tool.letter}
					/>
				{/each}
			</div>
		</div>

		<!-- Frameworks -->
		<div>
			<h3 class="label mb-3">Frameworks</h3>
			<div class="grid grid-cols-2 md:grid-cols-4 gap-3">
				{#each frameworks as tool}
					{@const tone = colorClasses[tool.color]}
					<OverviewTile
						title={tool.name}
						description={tool.description}
						tone={tone}
						iconPath={tool.icon}
						letter={tool.letter}
					/>
				{/each}
			</div>
		</div>
	</div>
</Card>
