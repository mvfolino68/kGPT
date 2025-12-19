<script lang="ts">
	interface Props {
		icon: 'list' | 'topic' | 'groups' | 'cluster' | 'offsets' | 'success' | 'warning' | 'error';
		title: string;
		subtitle?: string;
		color?: 'green' | 'cyan' | 'violet' | 'amber' | 'red';
	}

	let { icon, title, subtitle, color = 'green' }: Props = $props();

	const colorClasses = {
		green: {
			bg: 'bg-emerald-500/20',
			border: 'border-emerald-500/30',
			text: 'text-emerald-400'
		},
		cyan: {
			bg: 'bg-cyan-500/20',
			border: 'border-cyan-500/30',
			text: 'text-cyan-400'
		},
		violet: {
			bg: 'bg-violet-500/20',
			border: 'border-violet-500/30',
			text: 'text-violet-400'
		},
		amber: {
			bg: 'bg-amber-500/20',
			border: 'border-amber-500/30',
			text: 'text-amber-400'
		},
		red: {
			bg: 'bg-red-500/20',
			border: 'border-red-500/30',
			text: 'text-red-400'
		}
	};

	const styles = $derived(colorClasses[color]);
</script>

<div class="flex items-center gap-2.5 mb-4">
	<div class="w-9 h-9 rounded-lg {styles.bg} flex items-center justify-center border {styles.border}">
		{#if icon === 'list'}
			<svg class="w-5 h-5 {styles.text}" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
				<path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 10h16M4 14h16M4 18h16" />
			</svg>
		{:else if icon === 'topic'}
			<svg class="w-5 h-5 {styles.text}" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
				<path stroke-linecap="round" stroke-linejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
			</svg>
		{:else if icon === 'groups'}
			<svg class="w-5 h-5 {styles.text}" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
				<path stroke-linecap="round" stroke-linejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
			</svg>
		{:else if icon === 'cluster'}
			<svg class="w-5 h-5 {styles.text}" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
				<path stroke-linecap="round" stroke-linejoin="round" d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
			</svg>
		{:else if icon === 'offsets'}
			<svg class="w-5 h-5 {styles.text}" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
				<path stroke-linecap="round" stroke-linejoin="round" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
			</svg>
		{:else if icon === 'success'}
			<svg class="w-5 h-5 {styles.text}" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
				<path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
			</svg>
		{:else if icon === 'warning'}
			<svg class="w-5 h-5 {styles.text}" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
				<path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
			</svg>
		{:else if icon === 'error'}
			<svg class="w-5 h-5 {styles.text}" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
				<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
			</svg>
		{/if}
	</div>
	<div>
		<span class="text-sm font-semibold {styles.text}">{title}</span>
		{#if subtitle}
			<p class="text-xs text-surface-500">{subtitle}</p>
		{/if}
	</div>
</div>

