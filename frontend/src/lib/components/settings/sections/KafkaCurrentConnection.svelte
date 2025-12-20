<script lang="ts">
	import { Icon, SectionHeader, InnerCard } from '$lib/components/ui';
	import type { ClusterInfo } from '$lib/api';

	interface Props {
		clusterInfo: Partial<ClusterInfo>;
	}

	let { clusterInfo }: Props = $props();
</script>

<InnerCard padding="md">
	<div class="flex items-center justify-between mb-2">
		<SectionHeader variant="highlight" spacing="none">Current Connection</SectionHeader>
		<div class="flex items-center gap-2">
			<span class="relative flex h-2 w-2">
				<span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
				<span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
			</span>
			<span class="text-xs text-emerald-500 font-medium">Connected</span>
		</div>
	</div>
	<div>
		<p class="text-sm font-medium text-text">{clusterInfo.cluster_id || 'Connected Cluster'}</p>
		<p class="text-xs text-text-tertiary mt-0.5">
			{clusterInfo.brokers || 0} broker(s) | {clusterInfo.topics?.length || 0} topics
		</p>
	</div>
</InnerCard>
