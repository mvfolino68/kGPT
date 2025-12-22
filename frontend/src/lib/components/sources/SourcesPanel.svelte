<script lang="ts">
	import type { Source, SourceGroup } from './types';
	import { groupSourcesByType } from './types';
	import SourceItem from './SourceItem.svelte';
	// SourceDrawer removed from here, hoisted to layout
	import { Button, Icon, ExpandableGroup } from '$lib/components/ui';
	import { openSourceDrawer } from '$lib/stores/chat';

	interface Props {
		sources: Source[];
		isStreaming?: boolean;
		/** When true, hides the collapsible header and shows sources directly */
		inline?: boolean;
	}

	let { sources, isStreaming = false, inline = false }: Props = $props();

	// State - start expanded by default for better discoverability
	let isExpanded = $state(false);
	let expandedGroups = $state<Record<string, boolean>>(
		Object.fromEntries(groupSourcesByType(sources).map((g) => [g.type, false]))
	);
	let hasInitialized = $state(true);

	// Derived
	const groups = $derived(groupSourcesByType(sources));
	const totalSources = $derived(sources.length);
	const hasMultipleTypes = $derived(groups.length > 1);

	// Auto-initialize group states before render to avoid undefined bindings
	$effect.pre(() => {
		if (groups.length > 0) {
			groups.forEach(g => {
				if (expandedGroups[g.type] === undefined) {
					expandedGroups[g.type] = false;
				}
			});

			if (!hasInitialized) {
				expandedGroups[groups[0].type] = true;
				hasInitialized = true;
			}
		}
	});

	function toggleExpanded() {
		isExpanded = !isExpanded;
	}

	function toggleGroup(type: string) {
		expandedGroups = { ...expandedGroups, [type]: !expandedGroups[type] };
	}

	function handleSourceSelect(source: Source) {
		openSourceDrawer(source);
	}

	function getGroupColorClasses(color: string) {
		switch (color) {
			case 'emerald':
				return {
					text: 'text-blue-400',
					bg: 'bg-blue-500/10',
					border: 'border-blue-500/20',
					hover: 'hover:border-blue-500/40'
				};
			case 'blue':
				return {
					text: 'text-blue-400',
					bg: 'bg-blue-500/10',
					border: 'border-blue-500/20',
					hover: 'hover:border-blue-500/40'
				};
			case 'amber':
				return {
					text: 'text-amber-400',
					bg: 'bg-amber-500/10',
					border: 'border-amber-500/20',
					hover: 'hover:border-amber-500/40'
				};
			default:
				return {
					text: 'text-surface-400',
					bg: 'bg-surface-500/10',
					border: 'border-surface-500/20',
					hover: 'hover:border-surface-500/40'
				};
		}
	}

	// Track citation indices for proper numbering
	function getSourceIndex(source: Source): number {
		return sources.indexOf(source) + 1;
	}
</script>

{#if sources.length > 0 && !isStreaming}
	<div class="sources-panel {inline ? 'mt-2' : 'mt-4'}">
		<!-- Collapsed summary bar (hidden in inline mode) -->
		{#if !inline}
			<Button
				variant="ghost"
				size="lg"
				class="w-full justify-between gap-3 p-3 rounded-lg bg-surface-800/30 hover:bg-surface-800/50 border border-surface-700/50 hover:border-surface-600/50 transition-all duration-150 group"
				onclick={toggleExpanded}
			>
				<div class="flex items-center gap-3">
					<!-- Sources icon -->
					<div class="w-8 h-8 rounded-lg bg-surface-800 flex items-center justify-center
						group-hover:bg-surface-700 transition-colors">
						<svg class="w-4 h-4 text-surface-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
						</svg>
					</div>

					<div class="text-left">
						<div class="flex items-center gap-2">
							<span class="text-sm font-medium text-surface-200">
								{totalSources} {totalSources === 1 ? 'Source' : 'Sources'}
							</span>
							<!-- Type pills -->
							<!-- Type pills removed for collapsed view -->
						</div>
						<p class="text-[11px] text-surface-500 mt-0.5">
							{isExpanded ? 'Click to collapse' : 'Click to view sources used in this response'}
						</p>
					</div>
				</div>

				<!-- Expand/collapse icon -->
				<svg
					class="w-5 h-5 text-surface-500 transition-transform duration-200
						{isExpanded ? 'rotate-180' : ''}"
					fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"
				>
					<path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
				</svg>
			</Button>
		{/if}

		<!-- Expanded sources list (always shown in inline mode) -->
		{#if isExpanded || inline}
			<div class="mt-3 space-y-3 animate-fade-in">
				{#each groups as group}
					<ExpandableGroup
						title={group.label}
						count={group.sources.length}
						color={group.color === 'emerald' ? 'blue' : group.color as 'blue' | 'amber' | 'emerald' | 'default'}
						iconPath={group.icon}
						bind:expanded={expandedGroups[group.type]}
					>
						{#each group.sources as source}
							<SourceItem
								{source}
								index={getSourceIndex(source)}
								isExpanded={true}
								onSelect={handleSourceSelect}
							/>
						{/each}
					</ExpandableGroup>
				{/each}

				<!-- Educational footer -->
				<div class="p-3 rounded-lg bg-surface-800/20 border border-dashed border-surface-700/50">
					<div class="flex items-start gap-2">
						<Icon name="info" size="sm" class="text-surface-500 mt-0.5 flex-shrink-0" />
						<div>
							<p class="text-xs text-surface-400 leading-relaxed">
								<strong class="text-surface-300">How sources work:</strong>
								Citations numbered [1], [2], etc. in the response refer to these sources.
								Click any source to see the full content and understand why it was selected.
							</p>
						</div>
					</div>
				</div>
			</div>
		{/if}
	</div>
{/if}

<style>
	@keyframes fade-in {
		from {
			opacity: 0;
			transform: translateY(-4px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	.animate-fade-in {
		animation: fade-in 0.15s ease-out;
	}
</style>
