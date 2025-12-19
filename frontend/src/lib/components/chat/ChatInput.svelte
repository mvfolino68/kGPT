<script lang="ts">
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

<div class="bg-surface-800 p-6">
	<div class="max-w-4xl mx-auto space-y-2">
		<div class="bg-surface-700/50 rounded-lg overflow-hidden">
			<div class="flex items-end gap-3 p-3">
				<span class="text-primary-light text-lg pb-1">&gt;</span>
				<textarea
					bind:this={inputRef}
					bind:value
					oninput={(e) => onInput(e.currentTarget.value)}
					onkeydown={handleKeydown}
					placeholder="Enter command..."
					{disabled}
					rows="1"
					class="flex-1 bg-transparent text-surface-100 placeholder-surface-600 resize-none focus:outline-none disabled:opacity-50 text-sm"
					style="field-sizing: content; max-height: 150px;"
				></textarea>
				<button
					type="button"
					class="btn btn-primary btn-sm"
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
				</button>
			</div>
		</div>
		<p class="text-center text-xs text-surface-600">
			ENTER to send / SHIFT+ENTER for newline
		</p>
	</div>
</div>
