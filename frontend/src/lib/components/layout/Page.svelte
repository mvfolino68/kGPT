<script lang="ts">
	import { Header, HeaderStatus } from '$lib/components';
	import type { ComponentProps } from 'svelte';

	let {
		title,
		subtitle,
		loading = false,
		error = null,
		status = null,
		children,
		headerActions,
		subNavigation
	} = $props<{
		title: string;
		subtitle?: string;
		loading?: boolean;
		error?: string | null;
		status?: { connected: boolean; label?: string } | null;
		children?: any;
		headerActions?: any;
		subNavigation?: any;
	}>();
</script>

<div class="flex flex-col h-full bg-bg">
	<Header {title} {subtitle}>
		{#snippet actions()}
			<div class="flex items-center gap-4">
				{#if status}
					<HeaderStatus
						status={status.connected ? 'active' : 'inactive'}
						label={status.label || (status.connected ? 'Connected' : 'Disconnected')}
						pulse={status.connected}
					/>
				{/if}
				{#if headerActions}
					{@render headerActions()}
				{/if}
			</div>
		{/snippet}
	</Header>

	{#if subNavigation}
		<nav class="border-b border-white/5 bg-bg-elevated sticky top-0 z-10 backdrop-blur-md bg-opacity-80">
			<div class="px-6 max-w-7xl mx-auto">
				{@render subNavigation()}
			</div>
		</nav>
	{/if}

	<main class="flex-1 overflow-hidden relative">
		{#if loading && !children}
			<!-- Full page loading -->
			<div class="absolute inset-0 flex items-center justify-center">
				<div class="flex flex-col items-center gap-4 text-text-secondary">
					<div class="w-8 h-8 rounded-full border-2 border-primary border-t-transparent animate-spin" />
					<p>Loading...</p>
				</div>
			</div>
		{:else if error && !children}
			<!-- Full page error -->
			<div class="absolute inset-0 flex items-center justify-center">
				<div class="text-center max-w-md mx-auto p-8">
					<h3 class="text-lg font-medium text-error mb-2">Something went wrong</h3>
					<p class="text-text-secondary">{error}</p>
				</div>
			</div>
		{:else}
			<div class="h-full overflow-y-auto custom-scrollbar">
				<div class="max-w-7xl mx-auto p-6 space-y-6 animate-fade-in">
					{@render children?.()}
				</div>
			</div>
		{/if}
	</main>
</div>

<style>
	.custom-scrollbar {
		scrollbar-width: thin;
		scrollbar-color: var(--color-surface-active) transparent;
	}
	.custom-scrollbar::-webkit-scrollbar {
		width: 6px;
	}
	.custom-scrollbar::-webkit-scrollbar-track {
		background: transparent;
	}
	.custom-scrollbar::-webkit-scrollbar-thumb {
		background-color: var(--color-surface-active);
		border-radius: 20px;
	}
</style>
