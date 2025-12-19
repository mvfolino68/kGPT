<script lang="ts">
	import { Button, Icon } from '$lib/components/ui';
	import { onMount } from 'svelte';
	import { fade, fly } from 'svelte/transition';
	import { isHintDismissed, dismissHint } from './hintsStore.svelte';

	interface Props {
		id: string;
		title: string;
		description: string;
		position?: 'top' | 'bottom';
		delay?: number;
	}

	let { id, title, description, position = 'top', delay = 500 }: Props = $props();

	let visible = $state(false);
	let dismissed = $state(true);

	onMount(() => {
		dismissed = isHintDismissed(id);
		if (!dismissed) {
			setTimeout(() => {
				visible = true;
			}, delay);
		}
	});

	function handleDismiss() {
		visible = false;
		dismissHint(id);
		dismissed = true;
	}
</script>

{#if visible && !dismissed}
	<div
		class="fixed z-40 {position === 'top' ? 'top-20 right-6' : 'bottom-6 right-6'}"
		in:fly={{ y: position === 'top' ? -20 : 20, duration: 300 }}
		out:fade={{ duration: 150 }}
	>
		<div class="bg-surface-800 border border-surface-700/30 rounded-xl shadow-xl max-w-sm overflow-hidden">
			<div class="p-4">
				<div class="flex items-start gap-3">
					<!-- Icon -->
					<div class="w-10 h-10 rounded-lg bg-surface-700/50 flex items-center justify-center flex-shrink-0">
						<svg class="w-5 h-5 text-surface-300" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
							<path stroke-linecap="round" stroke-linejoin="round" d="M12 18v-5.25m0 0a6.01 6.01 0 001.5-.189m-1.5.189a6.01 6.01 0 01-1.5-.189m3.75 7.478a12.06 12.06 0 01-4.5 0m3.75 2.383a14.406 14.406 0 01-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 10-7.517 0c.85.493 1.509 1.333 1.509 2.316V18" />
						</svg>
					</div>

					<!-- Content -->
					<div class="flex-1 min-w-0">
						<h3 class="text-sm font-medium text-surface-100 mb-1">{title}</h3>
						<p class="text-xs text-surface-400 leading-relaxed">{description}</p>
					</div>

					<!-- Dismiss button -->
					<button
						type="button"
						class="btn-action btn-action-default flex-shrink-0"
						onclick={handleDismiss}
						aria-label="Dismiss hint"
					>
						<Icon name="close" size="sm" strokeWidth={2} />
					</button>
				</div>

				<!-- Got it button -->
				<div class="mt-3 flex justify-end">
					<Button variant="link" size="xs" onclick={handleDismiss}>
						Got it
					</Button>
				</div>
			</div>
		</div>
	</div>
{/if}
