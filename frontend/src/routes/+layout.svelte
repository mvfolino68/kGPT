<script lang="ts">
	import '../app.css';
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { health, refreshHealth } from '$lib/stores/health';
	import kgptLogo from '$lib/assets/kgpt-logo.svg';

	let { children } = $props();

	// Navigation items with icon identifiers
	const navItems = [
		{ href: '/', label: 'chat', iconType: 'chat' },
		{ href: '/documents', label: 'documents', iconType: 'docs' },
		{ href: '/cluster', label: 'cluster', iconType: 'kafka' },
		{ href: '/settings', label: 'settings', iconType: 'settings' }
	];

	onMount(() => {
		refreshHealth();
		// Refresh health every 30 seconds
		const interval = setInterval(refreshHealth, 30000);
		return () => clearInterval(interval);
	});
</script>

<svelte:head>
	<title>kGPT - Kafka Documentation Assistant</title>
	<link rel="icon" type="image/svg+xml" href="/favicon.svg" />
</svelte:head>

<div class="flex h-screen bg-surface-900">
	<!-- Sidebar - terminal style -->
	<aside class="w-56 bg-surface-800 flex flex-col border-r border-surface-700">
		<!-- Logo -->
		<div class="px-4 py-3 border-b border-surface-700">
			<div class="flex items-center gap-3">
				<img src={kgptLogo} alt="kGPT" class="w-8 h-8" />
				<div>
					<h1 class="font-mono text-lg text-surface-100 leading-tight">kGPT</h1>
					<p class="text-xs font-mono text-surface-500">kafka + AI</p>
				</div>
			</div>
		</div>

		<!-- Navigation -->
		<nav class="flex-1 py-2">
			{#each navItems as item}
				<a
					href={item.href}
					class="flex items-center gap-3 px-4 py-2.5 font-mono text-sm transition-colors
						{$page.url.pathname === item.href
						? 'bg-surface-700/50 text-emerald-400 border-l-2 border-emerald-400'
						: 'text-surface-400 hover:bg-surface-700/30 hover:text-surface-200 border-l-2 border-transparent'}"
				>
					{#if item.iconType === 'chat'}
						<!-- Terminal/Chat icon -->
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
						</svg>
					{:else if item.iconType === 'docs'}
						<!-- Documents icon -->
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
						</svg>
					{:else if item.iconType === 'kafka'}
						<!-- Kafka streaming icon -->
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<circle cx="12" cy="12" r="2" stroke-width="2"/>
							<circle cx="12" cy="5" r="1.5" stroke-width="2"/>
							<circle cx="6" cy="17" r="1.5" stroke-width="2"/>
							<circle cx="18" cy="17" r="1.5" stroke-width="2"/>
							<path stroke-linecap="round" stroke-width="2" d="M12 7v3M9.5 13.5l-2 2M14.5 13.5l2 2"/>
						</svg>
					{:else if item.iconType === 'settings'}
						<!-- Settings/Config icon -->
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
						</svg>
					{/if}
					<span>{item.label}</span>
				</a>
			{/each}
		</nav>

		<!-- Status - terminal style -->
		<div class="px-4 py-3 border-t border-surface-700 bg-surface-900/50">
			<p class="text-xs font-mono text-surface-600 mb-2"># status</p>
			{#if $health}
				<div class="space-y-1 text-xs font-mono">
					<div class="flex items-center gap-2">
						<span class="w-1.5 h-1.5 rounded-full {$health.qdrant_connected ? 'bg-emerald-400' : 'bg-red-400'}"></span>
						<span class="text-surface-400">qdrant:</span>
						<span class="{$health.qdrant_connected ? 'text-emerald-400' : 'text-red-400'}">
							{$health.qdrant_connected ? 'ok' : 'err'}
						</span>
					</div>
					<div class="flex items-center gap-2">
						<span class="w-1.5 h-1.5 rounded-full {$health.kafka_connected ? 'bg-emerald-400' : 'bg-amber-400'}"></span>
						<span class="text-surface-400">kafka:</span>
						<span class="{$health.kafka_connected ? 'text-emerald-400' : 'text-amber-400'}">
							{$health.kafka_connected ? 'ok' : '—'}
						</span>
					</div>
				</div>
			{:else}
				<p class="text-xs font-mono text-surface-600 animate-pulse">checking...</p>
			{/if}
		</div>
	</aside>

	<!-- Main content -->
	<main class="flex-1 overflow-hidden">
		{@render children()}
	</main>
</div>
