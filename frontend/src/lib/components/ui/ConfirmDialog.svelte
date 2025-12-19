<script lang="ts">
  import { Button, Input } from '$lib/components/ui';
  import StatusMessage from './StatusMessage.svelte';

  interface Props {
    title: string;
    message: string;
    confirmText?: string;
    confirmLabel?: string;
    cancelLabel?: string;
    variant?: 'danger' | 'warning';
    isLoading?: boolean;
    onConfirm: () => void;
    onCancel: () => void;
  }

  let {
    title,
    message,
    confirmText,
    confirmLabel = 'Confirm',
    cancelLabel = 'Cancel',
    variant = 'danger',
    isLoading = false,
    onConfirm,
    onCancel
  }: Props = $props();

  let confirmInput = $state('');
  let isConfirmDisabled = $derived(confirmText ? confirmInput !== confirmText : false);
</script>

<div class="space-y-4">
  <div class="space-y-2">
    <h3 class="text-lg font-medium text-text">{title}</h3>
    <p class="text-sm text-text-secondary">{message}</p>
  </div>

  {#if confirmText}
    <div class="space-y-2">
      <label for="confirm-input" class="text-xs font-medium text-text-tertiary">
        Type <span class="font-mono text-text select-all">{confirmText}</span> to confirm
      </label>
      <Input
        id="confirm-input"
        type="text"
        bind:value={confirmInput}
        placeholder={confirmText}
        autocomplete="off"
      />
    </div>
  {/if}

  <div class="flex items-center justify-end gap-3 pt-2">
    <Button
      variant="ghost"
      onclick={onCancel}
      disabled={isLoading}
    >
      {cancelLabel}
    </Button>
    <Button
      variant={variant}
      onclick={onConfirm}
      disabled={isConfirmDisabled || isLoading}
      loading={isLoading}
    >
      {confirmLabel}
    </Button>
  </div>
</div>
