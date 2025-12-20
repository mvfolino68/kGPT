<script lang="ts">
    import { educationalStore } from '$lib/stores/educational.svelte';
    import { fade, scale } from 'svelte/transition';

    // Derived state for easier access
    const pendingAction = $derived(educationalStore.pendingAction);

    function handleConfirm() {
        educationalStore.confirmAction();
    }

    function handleCancel() {
        educationalStore.cancelAction();
    }
</script>

{#if pendingAction}
    <div
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
        transition:fade={{ duration: 200 }}
    >
        <div
            class="bg-background border border-border rounded-xl shadow-2xl max-w-lg w-full overflow-hidden flex flex-col"
            transition:scale={{ duration: 200, start: 0.95 }}
        >
            <!-- Header -->
            <div class="p-6 border-b border-border bg-muted/30">
                <div class="flex items-center gap-3 mb-2">
                    <div class="w-2 h-2 rounded-full bg-primary animate-pulse"></div>
                    <span class="text-xs font-mono font-medium text-primary uppercase tracking-wider">Educational Mode</span>
                </div>
                <h3 class="text-xl font-bold text-foreground">
                    Action Intercepted: {pendingAction.type.toUpperCase()} {pendingAction.resource.toUpperCase()}
                </h3>
            </div>

            <!-- Content -->
            <div class="p-6 space-y-6">
                <!-- Explanation -->
                <div class="space-y-2">
                    <h4 class="text-sm font-semibold text-muted-foreground uppercase tracking-wide">What's happening?</h4>
                    <p class="text-foreground leading-relaxed">
                        {pendingAction.explanation || `You are about to ${pendingAction.type} the ${pendingAction.resource} "${pendingAction.name}".`}
                    </p>
                </div>

                <!-- Protocol Translation -->
                <div class="bg-card border border-border rounded-lg p-4 space-y-3">
                    <div class="flex justify-between items-center">
                         <h4 class="text-sm font-semibold text-muted-foreground uppercase tracking-wide">Protocol Translation</h4>
                         <span class="text-xs font-mono text-muted-foreground bg-muted px-2 py-0.5 rounded">Kafka Protocol v3.0+</span>
                    </div>

                    <div class="font-mono text-sm space-y-2">
                        <div class="flex gap-4 p-2 bg-background rounded border border-border/50">
                            <span class="text-primary font-bold min-w-[120px]">RPC Call</span>
                            <span class="text-foreground">{pendingAction.protocolOperation || 'AdminClient.execute'}</span>
                        </div>

                        {#if pendingAction.details}
                        <div class="space-y-1 mt-2 p-2">
                            <span class="text-xs text-muted-foreground block mb-1">Payload:</span>
                            {#each Object.entries(pendingAction.details) as [key, value]}
                                <div class="flex gap-2 text-xs">
                                    <span class="text-blue-400">{key}:</span>
                                    <span class="text-green-400">{JSON.stringify(value)}</span>
                                </div>
                            {/each}
                        </div>
                        {/if}
                    </div>
                </div>
            </div>

            <!-- Footer -->
            <div class="p-6 border-t border-border bg-muted/10 flex justify-end gap-3">
                <button
                    class="px-4 py-2 rounded-lg text-sm font-medium hover:bg-muted/50 transition-colors"
                    onclick={handleCancel}
                >
                    Cancel
                </button>
                <button
                    class="px-4 py-2 rounded-lg text-sm font-medium bg-primary text-primary-foreground hover:opacity-90 transition-opacity shadow-lg shadow-primary/20"
                    onclick={handleConfirm}
                >
                    Proceed & Execute
                </button>
            </div>
        </div>
    </div>
{/if}
