/**
 * Hints state management.
 * Tracks which contextual hints have been dismissed, persisted to localStorage.
 */

const STORAGE_KEY = 'kgpt-dismissed-hints';

interface HintsState {
	dismissedHints: Set<string>;
	loaded: boolean;
}

let state = $state<HintsState>({
	dismissedHints: new Set(),
	loaded: false
});

/**
 * Load dismissed hints from localStorage.
 */
export function loadHints(): void {
	if (state.loaded) return;

	try {
		const stored = localStorage.getItem(STORAGE_KEY);
		if (stored) {
			const parsed = JSON.parse(stored);
			if (Array.isArray(parsed)) {
				state.dismissedHints = new Set(parsed);
			}
		}
	} catch {
		// Ignore parse errors
	}

	state.loaded = true;
}

/**
 * Check if a hint has been dismissed.
 */
export function isHintDismissed(hintId: string): boolean {
	loadHints();
	return state.dismissedHints.has(hintId);
}

/**
 * Dismiss a hint.
 */
export function dismissHint(hintId: string): void {
	loadHints();
	state.dismissedHints.add(hintId);
	saveHints();
}

/**
 * Reset all hints (show them again).
 */
export function resetHints(): void {
	state.dismissedHints = new Set();
	saveHints();
}

/**
 * Dismiss all hints.
 */
export function dismissAllHints(): void {
	// Add all known hint IDs
	const allHints = ['dashboard', 'architecture', 'documents', 'settings'];
	allHints.forEach((id) => state.dismissedHints.add(id));
	saveHints();
}

function saveHints(): void {
	try {
		const arr = Array.from(state.dismissedHints);
		localStorage.setItem(STORAGE_KEY, JSON.stringify(arr));
	} catch {
		// Ignore storage errors
	}
}

/**
 * Get current hints state (reactive).
 */
export function getHintsState(): HintsState {
	loadHints();
	return state;
}
