<script lang="ts">
	interface Props {
		onConnectDemo: () => void;
	}

	let { onConnectDemo }: Props = $props();
</script>

<div class="bg-surface-900 border border-surface-700/50 rounded-lg overflow-hidden">
	<div class="flex items-center gap-2 px-4 py-3 border-b border-surface-700/50">
		<svg class="w-4 h-4 text-primary-light" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
			<path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
		</svg>
		<span class="text-[10px] font-bold text-surface-500 uppercase tracking-wider">Quick Connect</span>
	</div>

	<div class="p-4 space-y-3">
		<button type="button" class="btn btn-default w-full" onclick={onConnectDemo}>
			Demo Cluster <span class="text-surface-500 ml-1">(docker)</span>
		</button>
		<p class="text-xs text-surface-600">
			Running: docker compose --profile demo up?
		</p>
	</div>
</div>
