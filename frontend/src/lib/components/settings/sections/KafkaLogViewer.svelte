<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { Button } from '$lib/components/ui';
	import { Icon } from '$lib/components';

	import { chatMessages, pendingChatAction } from '$lib/stores/chat';
	let logs: string[] = $state([]);
	let ws: WebSocket | null = null;
	let autoScroll = $state(true);
	let logContainer: HTMLDivElement;

	function connect() {
		// Calculate WS URL from current location (handles both dev proxy and prod)
		const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
		const host = window.location.host;
		const wsUrl = `${protocol}//${host}/api/logs/kafka/ws`;

		ws = new WebSocket(wsUrl);

		ws.onmessage = (event) => {
			logs = [...logs, event.data];
			if (logs.length > 1000) {
				logs = logs.slice(logs.length - 1000); // Keep last 1000 lines
			}
			if (autoScroll) {
				scrollToBottom();
			}
		};

		ws.onclose = () => {
			setTimeout(connect, 2000); // Reconnect
		};
	}

	function scrollToBottom() {
		if (logContainer) {
			// user tick to wait for DOM update
			setTimeout(() => {
				logContainer.scrollTop = logContainer.scrollHeight;
			}, 0);
		}
	}

	function clearLogs() {
		logs = [];
	}

	function copyLogs() {
		navigator.clipboard.writeText(logs.join('\n'));
	}

	onMount(() => {
		connect();
	});

	onDestroy(() => {
		if (ws) {
			ws.close();
		}
	});
</script>

<div class="border border-border rounded-lg overflow-hidden bg-[#1e1e1e] font-mono text-sm shadow-sm">
	<!-- Toolbar -->
	<div class="flex items-center justify-between px-3 py-2 bg-secondary/30 border-b border-border">
		<div class="flex items-center gap-2">
			<span class="text-text-secondary text-xs font-semibold uppercase tracking-wider">Kafka Debug Logs</span>
			<div class="w-2 h-2 rounded-full {ws?.readyState === 1 ? 'bg-green-500' : 'bg-red-500'}"></div>
		</div>

		<div class="flex items-center gap-2">
			<button
				class="text-xs text-text-tertiary hover:text-text px-2 py-1 rounded transition-colors"
				onclick={() => autoScroll = !autoScroll}
			>
				{autoScroll ? 'Auto-scroll On' : 'Auto-scroll Off'}
			</button>
			<button
				class="text-xs text-text-tertiary hover:text-text px-2 py-1 rounded transition-colors"
				onclick={copyLogs}
				title="Copy to clipboard"
			>
				<Icon name="copy" size="xs" />
			</button>
			<button
				class="text-xs text-text-tertiary hover:text-text px-2 py-1 rounded transition-colors"
				onclick={clearLogs}
				title="Clear logs"
			>
				<Icon name="trash-2" size="xs" />
			</button>
			<div class="w-px h-4 bg-border mx-1"></div>
			<Button
				variant="primary"
				size="xs"
				onclick={() => {
					pendingChatAction.set({
						message: 'Analyze the recent Kafka debug logs for any errors or issues.',
						newSession: true
					});
				}}
			>
				<Icon name="sparkles" size="xs" />
				Analyze
			</Button>
		</div>
	</div>

	<!-- Log Content -->
	<div
		bind:this={logContainer}
		class="h-64 overflow-y-auto p-4 space-y-1"
	>
		{#if logs.length === 0}
			<div class="text-text-tertiary italic text-center py-8">No logs yet...</div>
		{/if}
		{#each logs as log}
			<div class="break-all whitespace-pre-wrap text-text-secondary font-mono text-xs hover:bg-white/5 px-1 rounded">
				{log}
			</div>
		{/each}
	</div>
</div>
