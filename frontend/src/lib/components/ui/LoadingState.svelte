<script lang="ts">
  import LoadingSpinner from './LoadingSpinner.svelte';

  interface Props {
    message?: string;
    showSpinner?: boolean;
    size?: 'sm' | 'md' | 'lg' | 'xl';
    class?: string;
  }

  let {
    message = 'Loading...',
    showSpinner = true,
    size = 'md',
    class: className = ''
  }: Props = $props();

  const textSizes = {
    xs: 'text-xs',
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg',
    xl: 'text-xl'
  };
</script>

<div class="flex flex-col items-center justify-center gap-3 p-4 text-text-secondary {className}">
  {#if showSpinner}
    <LoadingSpinner {size} />
  {/if}
  {#if message}
    <span class="{textSizes[size]} font-medium animate-pulse">{message}</span>
  {/if}
</div>
