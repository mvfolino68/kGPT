<script lang="ts">
	import { page } from '$app/stores';
	import { health } from '$lib/stores/health';
	import { NavLink, Icon, StatusDot, Tooltip } from '$lib/components/ui';
	import kgptLogo from '$lib/assets/kgpt-logo.svg';

	interface NavItem {
		href: string;
		label: string;
		icon: 'message' | 'cpu' | 'database' | 'settings';
		tooltip: string;
	}

	const navItems: NavItem[] = [
		{
			href: '/dashboard',
			label: 'Dashboard',
			icon: 'message',
			tooltip: 'Chat with your Kafka cluster using natural language AI'
		},
		{
			href: '/architecture',
			label: 'Architecture',
			icon: 'cpu',
			tooltip: 'See how multi-agent RAG orchestration routes your queries'
		},
		{
			href: '/documents',
			label: 'Vector Store',
			icon: 'database',
			tooltip: 'Manage documents, embeddings, and the Qdrant vector database'
		},
		{
			href: '/settings',
			label: 'Settings',
			icon: 'settings',
			tooltip: 'Configure API keys, Kafka clusters, and preferences'
		}
	];

	let hoveredItem = $state<string | null>(null);
</script>

<aside class="w-64 bg-bg-elevated flex flex-col border-r border-border-subtle h-screen transition-all duration-300">
	<!-- Logo -->
	<div class="px-5 py-6">
		<a href="/dashboard" class="flex items-center gap-3 group">
			<div class="w-10 h-10 rounded-xl bg-surface-active flex items-center justify-center shadow-md group-hover:scale-105 transition-transform duration-300">
				<img src={kgptLogo} alt="kGPT" class="w-6 h-6" />
			</div>
			<div>
				<h1 class="text-xl font-bold text-text leading-tight tracking-tight group-hover:text-primary transition-colors">kGPT</h1>
				<p class="text-xs text-text-tertiary">Kafka Management</p>
			</div>
		</a>
	</div>

	<!-- Navigation -->
	<nav class="flex-1 py-4 px-3 space-y-1.5 overflow-y-auto">
		<!-- Main Nav -->
		<div class="space-y-1">
			<div class="px-3 py-1 text-xs font-medium text-text-tertiary uppercase tracking-wider">Menu</div>
			{#each navItems as item}
				{@const isActive = $page.url.pathname === item.href || $page.url.pathname.startsWith(item.href + '/')}
				<Tooltip text={item.tooltip} position="right" delay={300} class="w-full">
					<NavLink href={item.href} active={isActive}>
						<Icon name={item.icon} size="md" />
						<span class="font-medium">{item.label}</span>
						{#if isActive}
							<div class="ml-auto w-1.5 h-1.5 rounded-full bg-primary shadow-glow-primary"></div>
						{/if}
					</NavLink>
				</Tooltip>
			{/each}
		</div>
	</nav>

	<!-- Status Footer -->
	<div class="p-4 border-t border-border-subtle bg-surface/30 backdrop-blur-sm">
		<div class="flex items-center justify-between mb-3">
			<div class="text-xs font-semibold text-text-tertiary uppercase tracking-wider">System Health</div>
			{#if !$health}
				<div class="w-2 h-2 rounded-full bg-text-tertiary animate-pulse"></div>
			{/if}
		</div>

		{#if $health}
			<div class="space-y-2">
				<Tooltip text="Vector Database Status" position="top" class="w-full">
					<a href="/documents" class="flex items-center justify-between text-sm p-2 rounded-lg hover:bg-surface-active/50 transition-all border border-transparent hover:border-border-subtle group">
						<div class="flex items-center gap-2.5">
							<div class="w-6 h-6 rounded-md bg-surface flex items-center justify-center group-hover:bg-bg-elevated transition-colors">
								<Icon name="database" size="sm" class="text-text-secondary" />
							</div>
							<span class="text-text-secondary group-hover:text-text transition-colors">Qdrant</span>
						</div>
						<StatusDot status={$health.qdrant_connected ? 'success' : 'error'} size="sm" pulse={$health.qdrant_connected} />
					</a>
				</Tooltip>

				<Tooltip text="Kafka Cluster Status" position="top" class="w-full">
					<a href="/dashboard" class="flex items-center justify-between text-sm p-2 rounded-lg hover:bg-surface-active/50 transition-all border border-transparent hover:border-border-subtle group">
						<div class="flex items-center gap-2.5">
							<div class="w-6 h-6 rounded-md bg-surface flex items-center justify-center group-hover:bg-bg-elevated transition-colors">
								<Icon name="cpu" size="sm" class="text-text-secondary" />
							</div>
							<span class="text-text-secondary group-hover:text-text transition-colors">Kafka</span>
						</div>
						<StatusDot status={$health.kafka_connected ? 'success' : 'inactive'} size="sm" pulse={$health.kafka_connected} />
					</a>
				</Tooltip>
			</div>
		{:else}
			<div class="flex flex-col gap-2 animate-pulse">
				<div class="h-8 bg-surface rounded-lg w-full"></div>
				<div class="h-8 bg-surface rounded-lg w-full"></div>
			</div>
		{/if}
	</div>
</aside>
