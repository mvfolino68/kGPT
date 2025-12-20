import { browser } from '$app/environment';

export interface PendingAction {
    type: 'create' | 'delete' | 'update' | 'custom';
    resource: 'topic' | 'group' | 'config' | 'cluster';
    name: string;
    details?: Record<string, any>;
    explanation?: string;
    protocolOperation?: string; // e.g., "CreateTopics (API Key 19)"
    onConfirm: () => Promise<void>;
}

class EducationalStore {
    learningMode = $state(false);
    pendingAction = $state<PendingAction | null>(null);

    constructor() {
        if (browser) {
            const stored = localStorage.getItem('kgpt_learning_mode');
            if (stored) {
                this.learningMode = stored === 'true';
            }
        }
    }

    toggleLearningMode() {
        this.learningMode = !this.learningMode;
        if (browser) {
            localStorage.setItem('kgpt_learning_mode', String(this.learningMode));
        }
    }

    // Trigger an action. If learning mode is on, it sets pendingAction.
    // If off, it executes immediately.
    async performAction(action: PendingAction) {
        if (this.learningMode) {
            this.pendingAction = action;
        } else {
            await action.onConfirm();
        }
    }

    confirmAction() {
        if (this.pendingAction) {
            this.pendingAction.onConfirm();
            this.pendingAction = null;
        }
    }

    cancelAction() {
        this.pendingAction = null;
    }
}

export const educationalStore = new EducationalStore();
