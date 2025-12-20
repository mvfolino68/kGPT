<script lang="ts">
	interface Props {
		spacing?: 'none' | 'sm' | 'md' | 'lg';
		class?: string;
	}

	let { spacing = 'md', class: className = '' }: Props = $props();

	const spacingClasses = {
		none: 'my-0',
		sm: 'my-2',
		md: 'my-4',
		lg: 'my-6'
	};
</script>

<hr class="border-0 border-t border-surface-700/50 {spacingClasses[spacing]} {className}" />
