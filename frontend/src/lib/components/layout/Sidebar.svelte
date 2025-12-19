<script lang="ts">
	import { page } from '$app/stores';
	import { health } from '$lib/stores/health';
	import { NavLink, Icon, StatusDot } from '$lib/components/ui';
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

<aside class="w-56 bg-bg-elevated flex flex-col">
	<!-- Logo -->
	<div class="px-4 py-5">
		<a href="/dashboard" class="flex items-center gap-3 group">
			<div class="w-9 h-9 rounded-lg bg-surface flex items-center justify-center">
				<img src={kgptLogo} alt="kGPT" class="w-5 h-5" />
			</div>
			<div>
				<h1 class="text-lg font-semibold text-text leading-tight tracking-tight">kGPT</h1>
				<p class="text-xs text-text-tertiary">Kafka Management</p>
			</div>
		</a>
	</div>

	<!-- Navigation -->
	<nav class="flex-1 py-4 px-3 space-y-1">
		{#each navItems as item}
			{@const isActive = $page.url.pathname === item.href || $page.url.pathname.startsWith(item.href + '/')}
			<div
				class="relative group"
				role="presentation"
				onmouseenter={() => hoveredItem = item.href}
				onmouseleave={() => hoveredItem = null}
			>
				<NavLink href={item.href} active={isActive}>
					<Icon name={item.icon} size="md" />
					<span>{item.label}</span>
				</NavLink>

				<!-- Tooltip -->
				{#if hoveredItem === item.href}
					<div class="absolute left-full ml-2 top-0 z-50 pointer-events-none animate-fade-in">
						<div class="bg-surface-active text-text text-xs px-3 py-2 rounded-md shadow-lg max-w-[250px]">
							{item.tooltip}
							<div class="absolute right-full top-3 -mr-1 w-2 h-2 bg-surface-active rotate-45"></div>
						</div>
					</div>
				{/if}
			</div>
		{/each}
	</nav>

	<!-- Status Footer -->
	<div class="px-4 py-4 space-y-2">
		<div class="label mb-3">System Status</div>

		{#if $health}
			<div class="space-y-2">
				<a href="/documents" class="flex items-center justify-between text-sm py-1.5 px-2 rounded-md hover:bg-surface transition-colors">
					<span class="text-text-secondary">Qdrant</span>
					<div class="flex items-center gap-2">
						<StatusDot status={$health.qdrant_connected ? 'success' : 'error'} size="sm" pulse={$health.qdrant_connected} />
						<span class="text-xs {$health.qdrant_connected ? 'text-success' : 'text-error'}">
							{$health.qdrant_connected ? 'Connected' : 'Offline'}
						</span>
					</div>
				</a>
				<a href="/dashboard" class="flex items-center justify-between text-sm py-1.5 px-2 rounded-md hover:bg-surface transition-colors">
					<span class="text-text-secondary">Kafka</span>
					<div class="flex items-center gap-2">
						<StatusDot status={$health.kafka_connected ? 'success' : 'inactive'} size="sm" pulse={$health.kafka_connected} />
						<span class="text-xs {$health.kafka_connected ? 'text-success' : 'text-text-tertiary'}">
							{$health.kafka_connected ? 'Connected' : 'Not connected'}
						</span>
					</div>
				</a>
			</div>
		{:else}
			<div class="flex items-center gap-2 text-sm text-text-tertiary">
				<span class="w-2 h-2 rounded-full bg-text-tertiary animate-pulse"></span>
				<span>Checking...</span>
			</div>
		{/if}
	</div>
</aside>
