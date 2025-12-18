<script lang="ts">
	import { RetroButton, RetroCard } from '$lib/components';

	interface Props {
		value: string;
		disabled: boolean;
		onSend: () => void;
		onInput: (value: string) => void;
	}

	let { value = $bindable(), disabled, onSend, onInput }: Props = $props();
	let inputRef: HTMLTextAreaElement;

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault();
			onSend();
		}
	}

	export function focus() {
		inputRef?.focus();
	}
</script>

<div class="border-t retro-border bg-surface-900/60 backdrop-blur-sm p-6">
	<div class="max-w-4xl mx-auto space-y-2">
		<RetroCard variant="elevated" class="!p-0">
			<div class="flex items-end gap-3 p-3 focus-within:border-glow-blue">
				<span class="text-blue-400 font-mono text-lg pb-1">></span>
				<textarea
					bind:this={inputRef}
					bind:value
					oninput={(e) => onInput(e.currentTarget.value)}
					onkeydown={handleKeydown}
					placeholder="Enter command..."
					{disabled}
					rows="1"
					class="flex-1 bg-transparent text-surface-100 placeholder-surface-600 resize-none focus:outline-none disabled:opacity-50 text-sm font-mono"
					style="field-sizing: content; max-height: 150px;"
				></textarea>
				<RetroButton
					variant="primary"
					size="sm"
					onclick={onSend}
					disabled={disabled || !value.trim()}
				>
					{#if disabled}
						<svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
							<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
							<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
						</svg>
					{:else}
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
						</svg>
					{/if}
				</RetroButton>
			</div>
		</RetroCard>
		<p class="text-center text-xs text-surface-600 font-mono">
			[ENTER] send | [SHIFT+ENTER] newline
		</p>
	</div>
</div>
