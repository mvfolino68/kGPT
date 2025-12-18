<script lang="ts">
	interface Props {
		variant?: 'default' | 'elevated' | 'glow-green' | 'glow-cyan' | 'glow-amber' | 'glow-blue' | 'confluent';
		class?: string;
		noPadding?: boolean;
		children: any;
	}

	let {
		variant = 'default',
		class: className = '',
		noPadding = false,
		children
	}: Props = $props();

	const variantClasses = {
		default: 'retro-card',
		elevated: 'retro-card-elevated',
		'glow-green': 'retro-card retro-card-glow-green',
		'glow-cyan': 'retro-card retro-card-glow-cyan',
		'glow-amber': 'retro-card border-glow-amber',
		'glow-blue': 'retro-card retro-card-glow-blue',
		'confluent': 'retro-card retro-card-confluent'
	};
</script>

<div class="{variantClasses[variant]} rounded-lg {noPadding ? '' : 'p-4'} {className}">
	{@render children()}
</div>

