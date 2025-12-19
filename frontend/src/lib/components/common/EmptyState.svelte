<script lang="ts">
  import type { Snippet } from 'svelte';
  import { Icon } from '$lib/components/ui';

  interface Props {
    title: string;
    description?: string;
    icon?: string;
    iconSnippet?: Snippet;
    class?: string;
    children?: Snippet;
  }

  let {
    title,
    description,
    icon,
    iconSnippet,
    class: className = '',
    children
  }: Props = $props();
</script>

<div class="flex flex-col items-center justify-center py-12 px-4 text-center {className}">
  {#if iconSnippet}
    {@render iconSnippet()}
  {:else if icon}
    <div class="bg-surface-elevated p-4 rounded-full mb-4 ring-1 ring-border-subtle shadow-sm">
      <Icon name={icon} class="w-8 h-8 text-text-tertiary" />
    </div>
  {/if}

  <h3 class="text-text font-medium text-lg mb-1">{title}</h3>

  {#if description}
    <p class="text-text-tertiary text-sm max-w-sm mb-6">{description}</p>
  {/if}

  {#if children}
    {@render children()}
  {/if}
</div>
