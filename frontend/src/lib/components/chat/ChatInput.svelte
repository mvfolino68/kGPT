<script lang="ts">
	import { Button, Icon } from '$lib/components/ui';

	interface Props {
		value: string;
		isProcessing: boolean;
		onSend: (message: string) => void;
		onKeydown?: (event: KeyboardEvent) => void;
	}

	let { value = $bindable(), isProcessing, onSend, onKeydown }: Props = $props();
	let inputRef: HTMLTextAreaElement | null = $state(null);

	function handleKeydown(event: KeyboardEvent) {
		if (onKeydown) {
			onKeydown(event);
		} else if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault();
			onSend(value);
		}
	}

	export function focus() {
		inputRef?.focus();
	}
</script>

<div class="p-4 bg-surface-800 border-t border-surface-700/50">
	<div class="flex items-end gap-2">
		<textarea
			bind:this={inputRef}
			bind:value
			onkeydown={handleKeydown}
			placeholder="Ask about your cluster..."
			disabled={isProcessing}
			rows="1"
			class="flex-1 bg-surface-700/50 border-none rounded-md px-3 py-2 text-sm text-foreground placeholder:text-muted resize-none transition-all focus:outline-none focus:bg-surface-700 focus:ring-2 focus:ring-primary-600/50"
			style="field-sizing: content; max-height: 120px;"
		></textarea>
		<Button
			variant="primary"
			size="icon"
			onclick={() => onSend(value)}
			disabled={isProcessing || !value.trim()}
		>
			{#if isProcessing}
				<svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
					<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
					<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
				</svg>
			{:else}
				<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
				</svg>
			{/if}
		</Button>
	</div>
</div>
