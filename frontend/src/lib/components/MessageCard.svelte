<script lang="ts">
	interface Props {
		title?: string;
		iconType?: 'cluster' | 'info' | 'success' | 'warning' | 'error' | 'edit' | 'help' | 'check' | 'x';
		iconColor?: 'emerald' | 'blue' | 'violet' | 'amber' | 'red';
		children: any;
		class?: string;
		variant?: 'default' | 'info' | 'success' | 'warning' | 'error';
	}

	let { title, iconType, iconColor = 'emerald', children, class: className = '', variant = 'default' }: Props = $props();

	const variantStyles = {
		default: 'bg-surface-900/80 border-white/5',
		info: 'bg-surface-900/80 border-blue-500/30 shadow-lg shadow-blue-500/5',
		success: 'bg-surface-900/80 border-emerald-500/30 shadow-lg shadow-emerald-500/5',
		warning: 'bg-surface-900/80 border-amber-500/40 shadow-lg shadow-amber-500/10',
		error: 'bg-surface-900/80 border-red-500/30 shadow-lg shadow-red-500/5'
	};

	const iconColorStyles = {
		emerald: 'bg-emerald-500/20 text-emerald-400',
		blue: 'bg-blue-500/20 text-blue-400',
		violet: 'bg-violet-500/20 text-violet-400',
		amber: 'bg-amber-500/20 text-amber-400',
		red: 'bg-red-500/20 text-red-400'
	};
</script>

<div class="mt-4 p-5 rounded-xl backdrop-blur-sm {variantStyles[variant]} {className}">
	{#if title || iconType}
		<div class="flex items-center gap-2.5 mb-4">
			{#if iconType}
				<div class="w-9 h-9 rounded-lg flex items-center justify-center {iconColorStyles[iconColor]}">
					{#if iconType === 'cluster'}
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2" />
						</svg>
					{:else if iconType === 'info'}
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
						</svg>
					{:else if iconType === 'success' || iconType === 'check'}
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
						</svg>
					{:else if iconType === 'warning'}
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
						</svg>
					{:else if iconType === 'error' || iconType === 'x'}
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
						</svg>
					{:else if iconType === 'edit'}
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
						</svg>
					{:else if iconType === 'help'}
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
						</svg>
					{/if}
				</div>
			{/if}
			{#if title}
				<span class="text-sm font-semibold text-surface-200">{title}</span>
			{/if}
		</div>
	{/if}
	<div class="text-surface-200">
		{@render children()}
	</div>
</div>
