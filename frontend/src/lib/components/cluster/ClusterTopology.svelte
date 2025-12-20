<script lang="ts">
	import { onMount } from 'svelte';
	import { Card } from '$lib/components/ui';
	import TopologyNode from './TopologyNode.svelte';
	import TopologyConnection from './TopologyConnection.svelte';

	interface Props {
		brokers: number;
		topics: string[];
		consumerGroups: string[];
		connected: boolean;
	}

	let { brokers, topics, consumerGroups, connected }: Props = $props();

	let container: HTMLDivElement;
	let width = $state(800);
	let height = $state(400);

	const centerX = $derived(width / 2);
	const centerY = $derived(height / 2);

	const brokerNodes = $derived(() => {
		const nodes = [];
		const brokerRadius = 60;
		for (let i = 0; i < brokers; i++) {
			const angle = (2 * Math.PI * i) / Math.max(brokers, 1) - Math.PI / 2;
			nodes.push({
				id: `broker-${i}`,
				label: `Broker ${i + 1}`,
				x: centerX + brokerRadius * Math.cos(angle),
				y: centerY + brokerRadius * Math.sin(angle),
				type: 'broker' as const
			});
		}
		return nodes;
	});

	const topicNodes = $derived(() => {
		const displayTopics = topics.slice(0, 8);
		const spacing = Math.min(40, (height - 80) / Math.max(displayTopics.length, 1));
		const startY = centerY - ((displayTopics.length - 1) * spacing) / 2;

		return displayTopics.map((topic, i) => ({
			id: `topic-${i}`,
			label: topic.length > 15 ? topic.slice(0, 12) + '...' : topic,
			x: 120,
			y: startY + i * spacing,
			type: 'topic' as const
		}));
	});

	const consumerNodes = $derived(() => {
		const displayGroups = consumerGroups.slice(0, 6);
		const spacing = Math.min(50, (height - 80) / Math.max(displayGroups.length, 1));
		const startY = centerY - ((displayGroups.length - 1) * spacing) / 2;

		return displayGroups.map((group, i) => ({
			id: `consumer-${i}`,
			label: group.length > 15 ? group.slice(0, 12) + '...' : group,
			x: width - 120,
			y: startY + i * spacing,
			type: 'consumer' as const
		}));
	});

	const connections = $derived(() => {
		const lines: Array<{x1: number; y1: number; x2: number; y2: number; type: string}> = [];
		const brokerList = brokerNodes();
		const topicList = topicNodes();
		const consumerList = consumerNodes();

		topicList.forEach((topic, ti) => {
			const brokerIndex = ti % Math.max(brokerList.length, 1);
			if (brokerList[brokerIndex]) {
				lines.push({
					x1: topic.x + 60,
					y1: topic.y,
					x2: brokerList[brokerIndex].x - 20,
					y2: brokerList[brokerIndex].y,
					type: 'topic-broker'
				});
			}
		});

		consumerList.forEach((consumer, ci) => {
			const brokerIndex = ci % Math.max(brokerList.length, 1);
			if (brokerList[brokerIndex]) {
				lines.push({
					x1: brokerList[brokerIndex].x + 20,
					y1: brokerList[brokerIndex].y,
					x2: consumer.x - 60,
					y2: consumer.y,
					type: 'broker-consumer'
				});
			}
		});

		return lines;
	});

	onMount(() => {
		const observer = new ResizeObserver((entries) => {
			for (const entry of entries) {
				width = entry.contentRect.width;
				height = Math.max(300, Math.min(500, entry.contentRect.height));
			}
		});
		observer.observe(container);
		return () => observer.disconnect();
	});
</script>

<Card padding="none" class="w-full">
	{#snippet children()}
		<div bind:this={container} class="w-full h-[400px]">
			{#if !connected}
				<div class="flex items-center justify-center h-full">
					<div class="text-center">
						<svg class="w-16 h-16 mx-auto text-surface-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1">
							<path stroke-linecap="round" stroke-linejoin="round" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
						</svg>
						<p class="text-surface-400 text-sm">Connect to a cluster to view topology</p>
					</div>
				</div>
			{:else}
				<svg {width} {height} class="w-full h-full">
					<defs>
						<linearGradient id="connectionGradient" x1="0%" y1="0%" x2="100%" y2="0%">
							<stop offset="0%" style="stop-color:rgb(139 92 246);stop-opacity:0.6" />
							<stop offset="100%" style="stop-color:rgb(59 130 246);stop-opacity:0.6" />
						</linearGradient>
						<linearGradient id="consumerGradient" x1="0%" y1="0%" x2="100%" y2="0%">
							<stop offset="0%" style="stop-color:rgb(59 130 246);stop-opacity:0.6" />
							<stop offset="100%" style="stop-color:rgb(251 191 36);stop-opacity:0.6" />
						</linearGradient>
					</defs>

					{#each connections() as conn}
						<TopologyConnection {...conn} />
					{/each}

					{#each topicNodes() as node}
						<TopologyNode {...node} />
					{/each}

					{#each brokerNodes() as node}
						<TopologyNode {...node} />
					{/each}

					{#each consumerNodes() as node}
						<TopologyNode {...node} />
					{/each}

					<text x="120" y="30" text-anchor="middle" fill="rgb(148 163 184)" font-size="11" font-weight="500">TOPICS</text>
					<text x={centerX} y="30" text-anchor="middle" fill="rgb(148 163 184)" font-size="11" font-weight="500">BROKERS</text>
					<text x={width - 120} y="30" text-anchor="middle" fill="rgb(148 163 184)" font-size="11" font-weight="500">CONSUMERS</text>

					{#if topics.length > 8}
						<text x="120" y={height - 20} text-anchor="middle" fill="rgb(100 116 139)" font-size="10">+{topics.length - 8} more topics</text>
					{/if}
					{#if consumerGroups.length > 6}
						<text x={width - 120} y={height - 20} text-anchor="middle" fill="rgb(100 116 139)" font-size="10">+{consumerGroups.length - 6} more groups</text>
					{/if}
				</svg>
			{/if}
		</div>
	{/snippet}
</Card>
