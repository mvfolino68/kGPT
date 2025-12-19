<script lang="ts">
	import { getPathColor } from './types';

	interface Props {
		color: string;
		opacity?: number;
		roundedClass?: string;
		class?: string;
	}

	let { color, opacity = 0.1, roundedClass = 'rounded-lg', class: className = '' }: Props = $props();
</script>

<span
	class="pointer-events-none absolute inset-0 {getPathColor(color, 'bg')} {roundedClass} {className}"
	style="opacity: {opacity};"
	aria-hidden="true"
></span>

