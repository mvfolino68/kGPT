<script lang="ts">
	import { page } from '$app/stores';
	import { health } from '$lib/stores/health';
	import kgptLogo from '$lib/assets/kgpt-logo.svg';

	interface NavItem {
		href: string;
		label: string;
		icon: 'dashboard' | 'architecture' | 'vectorstore' | 'settings';
		tooltip: string;
	}

	const navItems: NavItem[] = [
		{
			href: '/dashboard',
			label: 'Dashboard',
			icon: 'dashboard',
			tooltip: 'Chat with your Kafka cluster using natural language AI'
		},
		{
			href: '/architecture',
			label: 'Architecture',
			icon: 'architecture',
			tooltip: 'See how multi-agent RAG orchestration routes your queries'
		},
		{
			href: '/documents',
			label: 'Vector Store',
			icon: 'vectorstore',
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

<aside class="w-56 bg-surface-900 flex flex-col">
	<!-- Logo -->
	<div class="px-4 py-5">
		<a href="/dashboard" class="flex items-center gap-3 group">
			<div class="w-9 h-9 rounded-lg bg-surface-800 flex items-center justify-center">
				<img src={kgptLogo} alt="kGPT" class="w-5 h-5" />
			</div>
			<div>
				<h1 class="text-lg font-semibold text-surface-100 leading-tight tracking-tight">kGPT</h1>
				<p class="text-xs text-surface-500">Kafka Management</p>
			</div>
		</a>
	</div>

	<!-- Navigation -->
	<nav class="flex-1 py-4 px-3 space-y-1">
		{#each navItems as item}
			{@const isActive = $page.url.pathname === item.href || $page.url.pathname.startsWith(item.href + '/')}
			<div class="relative group">
				<a
					href={item.href}
					onmouseenter={() => hoveredItem = item.href}
					onmouseleave={() => hoveredItem = null}
					class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all
						{isActive
						? 'bg-surface-800 text-surface-100'
						: 'text-surface-400 hover:bg-surface-800/50 hover:text-surface-200'}"
				>
					{#if item.icon === 'dashboard'}
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
							<path stroke-linecap="round" stroke-linejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
						</svg>
					{:else if item.icon === 'architecture'}
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
							<path stroke-linecap="round" stroke-linejoin="round" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
						</svg>
					{:else if item.icon === 'vectorstore'}
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
							<path stroke-linecap="round" stroke-linejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" />
						</svg>
					{:else if item.icon === 'settings'}
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
							<path stroke-linecap="round" stroke-linejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" />
							<path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
						</svg>
					{/if}
					<span>{item.label}</span>
				</a>

				<!-- Tooltip -->
				{#if hoveredItem === item.href}
					<div class="absolute left-full ml-2 top-0 z-50 pointer-events-none">
						<div class="bg-surface-800 text-surface-200 text-xs px-3 py-2 rounded-lg shadow-xl max-w-[250px]">
							{item.tooltip}
							<div class="absolute right-full top-3 -mr-1 w-2 h-2 bg-surface-800 rotate-45"></div>
						</div>
					</div>
				{/if}
			</div>
		{/each}
	</nav>

	<!-- Status Footer -->
	<div class="px-4 py-4 space-y-2">
		<div class="text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-3">System Status</div>

		{#if $health}
			<div class="space-y-2">
				<a
					href="/documents"
					class="flex items-center justify-between text-sm cursor-pointer hover:bg-surface-800/50 rounded px-2 py-1 -mx-2 transition-colors group"
				>
					<span class="text-surface-400 group-hover:text-surface-300">Qdrant</span>
					<div class="flex items-center gap-2">
						<span class="w-2 h-2 rounded-full {$health.qdrant_connected ? 'bg-emerald-400/80' : 'bg-red-400/80'}"></span>
						<span class="text-xs {$health.qdrant_connected ? 'text-emerald-400/80' : 'text-red-400/80'}">
							{$health.qdrant_connected ? 'Connected' : 'Offline'}
						</span>
					</div>
				</a>
				<a
					href="/dashboard"
					class="flex items-center justify-between text-sm cursor-pointer hover:bg-surface-800/50 rounded px-2 py-1 -mx-2 transition-colors group"
				>
					<span class="text-surface-400 group-hover:text-surface-300">Kafka</span>
					<div class="flex items-center gap-2">
						<span class="w-2 h-2 rounded-full {$health.kafka_connected ? 'bg-emerald-400/80' : 'bg-surface-600'}"></span>
						<span class="text-xs {$health.kafka_connected ? 'text-emerald-400/80' : 'text-surface-500'}">
							{$health.kafka_connected ? 'Connected' : 'Not connected'}
						</span>
					</div>
				</a>
			</div>
		{:else}
			<div class="flex items-center gap-2 text-sm text-surface-500">
				<span class="w-2 h-2 rounded-full bg-surface-600"></span>
				<span>Checking...</span>
			</div>
		{/if}
	</div>
</aside>
