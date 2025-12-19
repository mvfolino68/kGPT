<script lang="ts">
  interface Props {
    onClose?: () => void;
    class?: string;
  }

  let { onClose, class: className = '' }: Props = $props();
</script>

<div
  class="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 transition-opacity {className}"
  onclick={onClose}
  role="button"
  tabindex="-1"
  aria-label="Close"
  onkeydown={(e) => e.key === 'Escape' && onClose?.()}
></div>
