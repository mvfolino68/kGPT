<script lang="ts">
	interface Props {
		clusterId?: string;
		brokers: number;
		topics: number;
		groups: number;
	}

	let { clusterId, brokers, topics, groups }: Props = $props();
</script>

<div class="grid grid-cols-4 gap-3">
	<div class="bg-surface-800/50 border border-surface-700/50 rounded-lg p-4 text-center">
		<div class="text-[10px] font-bold text-surface-500 uppercase tracking-wider mb-2">Cluster ID</div>
		<div class="text-sm text-emerald-400 truncate" title={clusterId}>
			{clusterId || '-'}
		</div>
	</div>
	<div class="bg-surface-800/50 border border-surface-700/50 rounded-lg p-4 text-center">
		<div class="text-[10px] font-bold text-surface-500 uppercase tracking-wider mb-2">Brokers</div>
		<div class="text-2xl font-bold text-cyan-400 tabular-nums">
			{brokers}
		</div>
	</div>
	<div class="bg-surface-800/50 border border-surface-700/50 rounded-lg p-4 text-center">
		<div class="text-[10px] font-bold text-surface-500 uppercase tracking-wider mb-2">Topics</div>
		<div class="text-2xl font-bold text-violet-400 tabular-nums">
			{topics}
		</div>
	</div>
	<div class="bg-surface-800/50 border border-surface-700/50 rounded-lg p-4 text-center">
		<div class="text-[10px] font-bold text-surface-500 uppercase tracking-wider mb-2">Groups</div>
		<div class="text-2xl font-bold text-amber-400 tabular-nums">
			{groups}
		</div>
	</div>
</div>
