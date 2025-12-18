<script lang="ts">
	import '../app.css';
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { health, refreshHealth } from '$lib/stores/health';
	import { StatusIndicator, RetroCard } from '$lib/components';
	import kgptLogo from '$lib/assets/kgpt-logo.svg';

	let { children } = $props();

	// Boot animation state
	let bootComplete = $state(false);

	// Navigation items
	const navItems = [
		{ href: '/', label: 'chat', icon: 'terminal' },
		{ href: '/documents', label: 'documents', icon: 'docs' },
		{ href: '/cluster', label: 'cluster', icon: 'kafka' },
		{ href: '/settings', label: 'settings', icon: 'settings' }
	];

	onMount(() => {
		// Quick boot animation
		setTimeout(() => { bootComplete = true; }, 200);

		refreshHealth();
		const interval = setInterval(refreshHealth, 30000);
		return () => clearInterval(interval);
	});
</script>

<svelte:head>
	<title>kGPT - Kafka Documentation Assistant</title>
	<link rel="icon" type="image/svg+xml" href="/favicon.svg" />
</svelte:head>

<div class="flex h-screen bg-surface-950 {bootComplete ? 'opacity-100' : 'opacity-0'}" style="transition: opacity 200ms ease">
	<!-- Retro Sidebar -->
	<aside class="w-60 bg-surface-900/80 backdrop-blur-xl flex flex-col border-r retro-border">
		<!-- Logo Header -->
		<div class="px-5 py-4 border-b retro-border-blue">
			<div class="flex items-center gap-3">
				<div class="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-500/20 to-cyan-500/20 flex items-center justify-center border retro-border-blue data-stream-glow">
					<img src={kgptLogo} alt="kGPT" class="w-6 h-6" />
				</div>
				<div>
					<h1 class="text-lg font-bold font-mono text-confluent-primary text-glow-blue leading-tight tracking-tight">kGPT</h1>
					<p class="text-[10px] font-mono text-surface-500 tracking-wider uppercase">kafka + ai</p>
				</div>
			</div>
		</div>

		<!-- Navigation -->
		<nav class="flex-1 py-3 px-2 space-y-1">
			{#each navItems as item}
				{@const isActive = $page.url.pathname === item.href}
				<a
					href={item.href}
					class="flex items-center gap-3 px-4 py-3 font-mono text-sm rounded transition-all duration-200
						{isActive
						? 'bg-blue-500/10 text-confluent-primary border retro-border-blue shadow-lg shadow-blue-500/10'
						: 'text-surface-400 hover:bg-surface-800/60 hover:text-surface-200 border border-transparent'}"
				>
					<!-- Retro bracket indicator for active -->
					<span class="w-4 text-xs {isActive ? 'text-confluent-primary' : 'text-transparent'}">
						{isActive ? '[' : ''}
					</span>

					<!-- Icon -->
					{#if item.icon === 'terminal'}
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
						</svg>
					{:else if item.icon === 'docs'}
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
						</svg>
					{:else if item.icon === 'kafka'}
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
							<circle cx="12" cy="12" r="2"/>
							<circle cx="12" cy="5" r="1.5"/>
							<circle cx="6" cy="17" r="1.5"/>
							<circle cx="18" cy="17" r="1.5"/>
							<path stroke-linecap="round" d="M12 7v3M9.5 13.5l-2 2M14.5 13.5l2 2"/>
						</svg>
					{:else if item.icon === 'settings'}
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
							<path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
						</svg>
					{/if}

					<span class="flex-1">{item.label}</span>

					<span class="w-4 text-xs {isActive ? 'text-confluent-primary' : 'text-transparent'}">
						{isActive ? ']' : ''}
					</span>
				</a>
			{/each}
		</nav>

		<!-- Status Panel -->
		<div class="px-4 py-4 border-t retro-border bg-surface-900/60">
			<div class="flex items-center gap-2 mb-3">
				<svg class="w-3.5 h-3.5 text-surface-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
				</svg>
				<span class="text-[10px] font-bold font-mono text-surface-500 uppercase tracking-widest">System</span>
			</div>
		{#if $health}
			<div class="space-y-2">
				<!-- Qdrant Status -->
				<RetroCard class="!p-0">
					<div class="flex items-center justify-between px-3 py-2">
						<div class="flex items-center gap-2.5">
							<StatusIndicator
								status={$health.qdrant_connected ? 'active' : 'error'}
								pulse={$health.qdrant_connected}
							/>
							<span class="text-surface-300 font-mono text-xs">qdrant</span>
						</div>
						<span class="font-mono text-xs {$health.qdrant_connected ? 'text-emerald-400' : 'text-red-400'}">
							{$health.qdrant_connected ? 'OK' : 'ERR'}
						</span>
					</div>
				</RetroCard>

				<!-- Kafka Status -->
				<RetroCard class="!p-0">
					<div class="flex items-center justify-between px-3 py-2">
						<div class="flex items-center gap-2.5">
							<StatusIndicator
								status={$health.kafka_connected ? 'active' : 'inactive'}
								pulse={$health.kafka_connected}
							/>
							<span class="text-surface-300 font-mono text-xs">kafka</span>
						</div>
						<span class="font-mono text-xs {$health.kafka_connected ? 'text-emerald-400' : 'text-surface-600'}">
							{$health.kafka_connected ? 'OK' : '--'}
						</span>
					</div>
				</RetroCard>
			</div>
		{:else}
			<RetroCard class="!p-0 animate-pulse-slow">
				<div class="flex items-center gap-2 px-3 py-2">
					<StatusIndicator status="inactive" />
					<span class="text-surface-500 text-xs font-mono">checking...</span>
				</div>
			</RetroCard>
		{/if}
		</div>
	</aside>

	<!-- Main content -->
	<main class="flex-1 overflow-hidden">
		{@render children()}
	</main>
</div>
