<script lang="ts">
	import { page } from '$app/stores';
	import { health } from '$lib/stores/health';
	import kgptLogo from '$lib/assets/kgpt-logo.svg';

	interface NavItem {
		href: string;
		label: string;
		icon: 'dashboard' | 'cluster' | 'architecture' | 'documents' | 'settings';
	}

	const navItems: NavItem[] = [
		{ href: '/dashboard', label: 'Dashboard', icon: 'dashboard' },
		{ href: '/cluster', label: 'Cluster', icon: 'cluster' },
		{ href: '/architecture', label: 'Architecture', icon: 'architecture' },
		{ href: '/documents', label: 'Documents', icon: 'documents' },
		{ href: '/settings', label: 'Settings', icon: 'settings' }
	];
</script>

<aside class="w-56 bg-surface-900 flex flex-col border-r border-surface-700/50">
	<!-- Logo -->
	<div class="px-4 py-5 border-b border-surface-700/50">
		<a href="/dashboard" class="flex items-center gap-3 group">
			<div class="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center border border-primary/20">
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
			<a
				href={item.href}
				class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all
					{isActive
					? 'bg-primary/10 text-primary-light border border-primary/20'
					: 'text-surface-400 hover:bg-surface-800/50 hover:text-surface-200 border border-transparent'}"
			>
				{#if item.icon === 'dashboard'}
					<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
						<path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
					</svg>
				{:else if item.icon === 'cluster'}
					<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
						<path stroke-linecap="round" stroke-linejoin="round" d="M5.25 14.25h13.5m-13.5 0a3 3 0 01-3-3m3 3a3 3 0 100 6h13.5a3 3 0 100-6m-16.5-3a3 3 0 013-3h13.5a3 3 0 013 3m-19.5 0a4.5 4.5 0 01.9-2.7L5.737 5.1a3.375 3.375 0 012.7-1.35h7.126c1.062 0 2.062.5 2.7 1.35l2.587 3.45a4.5 4.5 0 01.9 2.7m0 0a3 3 0 01-3 3m0 3h.008v.008h-.008v-.008zm0-6h.008v.008h-.008v-.008zm-3 6h.008v.008h-.008v-.008zm0-6h.008v.008h-.008v-.008z" />
					</svg>
				{:else if item.icon === 'architecture'}
					<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
						<path stroke-linecap="round" stroke-linejoin="round" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
					</svg>
				{:else if item.icon === 'documents'}
					<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
						<path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
					</svg>
				{:else if item.icon === 'settings'}
					<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
						<path stroke-linecap="round" stroke-linejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" />
						<path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
					</svg>
				{/if}
				<span>{item.label}</span>
			</a>
		{/each}
	</nav>

	<!-- Status Footer -->
	<div class="px-4 py-4 border-t border-surface-700/50 space-y-2">
		<div class="text-[10px] font-bold uppercase tracking-wider text-surface-500 mb-3">System Status</div>

		{#if $health}
			<div class="space-y-2">
				<div class="flex items-center justify-between text-sm">
					<span class="text-surface-400">Qdrant</span>
					<div class="flex items-center gap-2">
						<span class="w-2 h-2 rounded-full {$health.qdrant_connected ? 'bg-emerald-400' : 'bg-red-400'}"></span>
						<span class="text-xs {$health.qdrant_connected ? 'text-emerald-400' : 'text-red-400'}">
							{$health.qdrant_connected ? 'Connected' : 'Offline'}
						</span>
					</div>
				</div>
				<div class="flex items-center justify-between text-sm">
					<span class="text-surface-400">Kafka</span>
					<div class="flex items-center gap-2">
						<span class="w-2 h-2 rounded-full {$health.kafka_connected ? 'bg-emerald-400' : 'bg-surface-600'}"></span>
						<span class="text-xs {$health.kafka_connected ? 'text-emerald-400' : 'text-surface-500'}">
							{$health.kafka_connected ? 'Connected' : 'Not connected'}
						</span>
					</div>
				</div>
			</div>
		{:else}
			<div class="flex items-center gap-2 text-sm text-surface-500">
				<span class="w-2 h-2 rounded-full bg-surface-600"></span>
				<span>Checking...</span>
			</div>
		{/if}
	</div>
</aside>
