<script lang="ts">
	import WizardStep from '../WizardStep.svelte';

	interface Props {
		onComplete: () => void;
		hasCluster: boolean;
	}

	let { onComplete, hasCluster }: Props = $props();

	const exploreLinks = [
		{
			href: '/dashboard',
			icon: 'dashboard',
			title: 'Dashboard',
			description: 'Chat with your Kafka cluster'
		},
		{
			href: '/architecture',
			icon: 'architecture',
			title: 'Architecture',
			description: 'See how agents work together'
		},
		{
			href: '/documents',
			icon: 'documents',
			title: 'Vector Store',
			description: 'Add docs to enhance responses'
		}
	];
</script>

<WizardStep
	title="You're All Set!"
	subtitle="kGPT is ready to help you manage your Kafka infrastructure"
>
	{#snippet children()}
		<div class="max-w-sm mx-auto">
			<!-- Success indicator -->
			<div class="flex justify-center mb-8">
				<div class="w-20 h-20 rounded-full bg-emerald-500/10 flex items-center justify-center border-2 border-emerald-500/30">
					<svg class="w-10 h-10 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
					</svg>
				</div>
			</div>

			<!-- Status summary -->
			<div class="p-4 rounded-lg bg-surface-800/50 border border-surface-700/50 mb-4">
				<div class="space-y-2">
					<div class="flex items-center justify-between text-sm">
						<span class="text-surface-400">OpenAI API</span>
						<span class="text-emerald-400 flex items-center gap-1.5">
							<span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
							Connected
						</span>
					</div>
					<div class="flex items-center justify-between text-sm">
						<span class="text-surface-400">Kafka Cluster</span>
						{#if hasCluster}
							<span class="text-emerald-400 flex items-center gap-1.5">
								<span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
								Connected
							</span>
						{:else}
							<span class="text-surface-500 flex items-center gap-1.5">
								<span class="w-1.5 h-1.5 rounded-full bg-surface-600"></span>
								Not connected
							</span>
						{/if}
					</div>
				</div>
			</div>

			<!-- Tip about embeddings -->
			<div class="p-3 rounded-lg bg-amber-500/5 border border-amber-500/20 mb-6">
				<div class="flex items-start gap-2.5">
					<svg class="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
						<path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
					</svg>
					<p class="text-xs text-surface-400">
						<span class="text-amber-400 font-medium">Tip:</span> To use RAG with custom documents, configure embedding providers and optional API keys (Exa, Cohere) in <a href="/settings" onclick={onComplete} class="text-primary-light hover:underline">Settings</a>.
					</p>
				</div>
			</div>

			<!-- Quick links -->
			<div class="space-y-2">
				<p class="text-xs font-medium uppercase tracking-wider text-surface-500 mb-3">Explore kGPT</p>
				{#each exploreLinks as link}
					<a
						href={link.href}
						onclick={onComplete}
						class="flex items-center gap-3 p-3 rounded-lg bg-surface-800/30 border border-surface-700/50 hover:border-primary/50 hover:bg-surface-800 transition-all group"
					>
						<div class="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center">
							{#if link.icon === 'dashboard'}
								<svg class="w-4 h-4 text-primary-light" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
									<path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6z" />
								</svg>
							{:else if link.icon === 'architecture'}
								<svg class="w-4 h-4 text-primary-light" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
									<path stroke-linecap="round" stroke-linejoin="round" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2z" />
								</svg>
							{:else if link.icon === 'documents'}
								<svg class="w-4 h-4 text-primary-light" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
									<path stroke-linecap="round" stroke-linejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375" />
								</svg>
							{/if}
						</div>
						<div class="flex-1">
							<h3 class="text-sm font-medium text-surface-100 group-hover:text-primary-light">{link.title}</h3>
							<p class="text-xs text-surface-500">{link.description}</p>
						</div>
						<svg class="w-4 h-4 text-surface-600 group-hover:text-primary-light" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
							<path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
						</svg>
					</a>
				{/each}
			</div>
		</div>
	{/snippet}

	{#snippet actions()}
		<div class="flex justify-center">
			<button type="button" class="btn btn-primary px-8" onclick={onComplete}>
				Start Using kGPT
			</button>
		</div>
	{/snippet}
</WizardStep>
