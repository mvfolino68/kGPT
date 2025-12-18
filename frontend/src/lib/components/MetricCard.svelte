<script lang="ts">
	interface Props {
		value: string | number;
		label: string;
		class?: string;
	}

	let { value, label, class: className = '' }: Props = $props();
</script>

<div class="text-center {className}">
	<p class="text-3xl font-bold text-surface-100 font-mono mb-1">{value}</p>
	<span class="text-xs text-surface-500 uppercase tracking-wider">{label}</span>
</div>


