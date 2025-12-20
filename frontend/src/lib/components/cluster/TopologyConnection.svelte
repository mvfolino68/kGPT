<script lang="ts">
	interface Props {
		x1: number;
		y1: number;
		x2: number;
		y2: number;
		type: string; // 'topic-broker' | 'broker-consumer'
	}

	let { x1, y1, x2, y2, type }: Props = $props();

	const stroke = $derived(type === 'topic-broker' ? 'url(#connectionGradient)' : 'url(#consumerGradient)');
</script>

<path
	d="M {x1} {y1} C {(x1 + x2) / 2} {y1}, {(x1 + x2) / 2} {y2}, {x2} {y2}"
	fill="none"
	{stroke}
	stroke-width="2"
	opacity="0.5"
/>
