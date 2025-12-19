<script lang="ts">
  import { Icon } from '$lib/components/ui';

  type Variant = 'success' | 'error' | 'warning' | 'info';

  interface Props {
    variant?: Variant;
    title?: string;
    message: string;
    dismissible?: boolean;
    onDismiss?: () => void;
    class?: string;
    actions?: import('svelte').Snippet;
    children?: import('svelte').Snippet;
  }

  let {
    variant = 'info',
    title,
    message,
    dismissible = false,
    onDismiss,
    class: className = '',
    actions,
    children
  }: Props = $props();

  const styles = {
    success: {
      container: 'bg-success-bg/50 border-success/20 text-success',
      icon: 'check-circle'
    },
    error: {
      container: 'bg-error-bg/50 border-error/20 text-error',
      icon: 'x-circle'
    },
    warning: {
      container: 'bg-warning-bg/50 border-warning/20 text-warning',
      icon: 'alert-triangle'
    },
    info: {
      container: 'bg-info-bg/50 border-info/20 text-info',
      icon: 'info'
    }
  };

  const currentStyle = $derived(styles[variant]);
</script>

<div class="flex items-start gap-3 p-4 rounded-lg border {currentStyle.container} {className} animate-fade-in">
  <Icon name={currentStyle.icon} class="w-5 h-5 mt-0.5 shrink-0" />

  <div class="flex-1">
    {#if title}
      <h4 class="font-medium text-sm mb-1">{title}</h4>
    {/if}
    <div class="text-sm opacity-90">{message}</div>
    {#if children}
      <div class="mt-2">
        {@render children()}
      </div>
    {/if}
  </div>

  {#if actions}
    <div class="flex items-center gap-2">
      {@render actions()}
    </div>
  {/if}

  {#if dismissible}
    <button
      type="button"
      onclick={onDismiss}
      class="p-1 hover:bg-black/10 rounded transition-colors"
      aria-label="Dismiss"
    >
      <Icon name="x" class="w-4 h-4" />
    </button>
  {/if}
</div>
