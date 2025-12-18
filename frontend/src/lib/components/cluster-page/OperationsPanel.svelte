<script lang="ts">
	const operations = [
		{ label: 'create topic', icon: 'M12 4v16m8-8H4', color: 'text-emerald-400' },
		{ label: 'delete topic', icon: 'M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16', color: 'text-red-400' },
		{ label: 'alter config', icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z', color: 'text-primary-light' },
		{ label: 'add partitions', icon: 'M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z', color: 'text-violet-400' }
	];
</script>

<div class="pt-4 border-t border-surface-700/50">
	<div class="flex items-center gap-2 mb-3">
		<svg class="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
			<path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
		</svg>
		<span class="text-[10px] font-bold text-surface-500 uppercase tracking-wider">Available Operations</span>
	</div>
	<div class="grid grid-cols-2 gap-2">
		{#each operations as op}
			<a href="/" class="btn btn-ghost flex items-center gap-2 px-3 py-2 text-xs justify-start">
				<svg class="w-4 h-4 {op.color}" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d={op.icon} />
				</svg>
				<span>{op.label}</span>
			</a>
		{/each}
	</div>
	<div class="mt-3 px-3 py-2 bg-surface-800/50 border border-surface-700/50 rounded-lg">
		<p class="text-xs text-surface-600">
			Go to <a href="/" class="text-primary-light hover:underline">chat</a> to perform operations
		</p>
	</div>
</div>
