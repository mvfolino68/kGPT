<script lang="ts">
	import { Icon, IconButton, Backdrop } from '$lib/components/ui';

	interface Props {
		isOpen: boolean;
		title?: string;
		size?: 'sm' | 'md' | 'lg' | 'xl';
		children?: import('svelte').Snippet;
		onClose: () => void;
	}

	let { isOpen, title, size = 'md', children, onClose }: Props = $props();

	function handleKeydown(event: KeyboardEvent) {
		if (isOpen && event.key === 'Escape') {
			onClose();
		}
	}

	const maxWidthClasses = {
		sm: 'max-w-sm',
		md: 'max-w-md',
		lg: 'max-w-lg',
		xl: 'max-w-xl'
	};
</script>

<svelte:window onkeydown={handleKeydown} />

{#if isOpen}
	<!-- Modal backdrop -->
	<Backdrop {onClose} class="z-50 bg-black/60" />

	<!-- Modal content container -->
	<div class="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
		<!-- Modal content -->
		<div class="w-full {maxWidthClasses[size]} animate-fade-in pointer-events-auto">
			<div class="bg-surface-900 rounded-lg overflow-hidden shadow-2xl border border-surface-700">
				<!-- Header -->
				<div class="px-4 py-3 flex items-center justify-between bg-surface-800 border-b border-surface-700">
					<h3 class="text-sm font-semibold text-surface-100">
						{title}
					</h3>
					<IconButton
						variant="ghost"
						size="sm"
						class="text-surface-400 hover:text-surface-200 hover:bg-surface-700"
						onclick={onClose}
						ariaLabel="Close modal"
						title="Close"
					>
						<Icon name="close" size="sm" strokeWidth={2} />
					</IconButton>
				</div>

				<!-- Body -->
				<div class="p-4 max-h-[80vh] overflow-y-auto">
					{@render children?.()}
				</div>
			</div>
		</div>
	</div>
{/if}
