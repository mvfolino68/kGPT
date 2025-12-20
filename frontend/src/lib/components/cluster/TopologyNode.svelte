<script lang="ts">
	interface Props {
		x: number;
		y: number;
		label: string;
		type: 'broker' | 'topic' | 'consumer';
	}

	let { x, y, label, type }: Props = $props();

	const config = {
		broker: {
			fill: 'rgb(59 130 246 / 0.2)',
			stroke: 'rgb(59 130 246 / 0.6)',
			textFill: 'rgb(147 197 253)',
			fontSize: '10',
			isCircle: true
		},
		topic: {
			fill: 'rgb(139 92 246 / 0.15)',
			stroke: 'rgb(139 92 246 / 0.4)',
			textFill: 'rgb(196 181 253)',
			fontSize: '11'
		},
		consumer: {
			fill: 'rgb(251 191 36 / 0.15)',
			stroke: 'rgb(251 191 36 / 0.4)',
			textFill: 'rgb(253 224 71)',
			fontSize: '11'
		}
	};

	const current = $derived(config[type]);
</script>

<g transform="translate({x}, {y})">
	{#if current.isCircle}
		<circle
			r="18"
			fill={current.fill}
			stroke={current.stroke}
			stroke-width="2"
		/>
		<text
			x="0"
			y="4"
			text-anchor="middle"
			fill={current.textFill}
			font-size={current.fontSize}
			font-weight="600"
		>
			B{label.split(' ')[1]}
		</text>
	{:else}
		<rect
			x="-55"
			y="-14"
			width="110"
			height="28"
			rx="6"
			fill={current.fill}
			stroke={current.stroke}
			stroke-width="1"
		/>
		<text
			x="0"
			y="4"
			text-anchor="middle"
			fill={current.textFill}
			font-size={current.fontSize}
			font-family="JetBrains Mono, monospace"
		>
			{label}
		</text>
	{/if}
</g>
