/**
 * Onboarding state management.
 * Checks if the user needs to complete onboarding (no valid API key configured).
 * Persists completion status to localStorage.
 */

import { getSettings, validateApiKey } from '$lib/api';

const STORAGE_KEY = 'kgpt-onboarding-complete';

interface OnboardingState {
	checked: boolean;
	needsOnboarding: boolean;
	showWizard: boolean;
	loading: boolean;
}

let state = $state<OnboardingState>({
	checked: false,
	needsOnboarding: false,
	showWizard: false,
	loading: false
});

/**
 * Check if onboarding was previously completed.
 */
function wasOnboardingCompleted(): boolean {
	try {
		return localStorage.getItem(STORAGE_KEY) === 'true';
	} catch {
		return false;
	}
}

/**
 * Check if onboarding is needed.
 * Returns true if no valid OpenAI API key is configured.
 */
export async function checkOnboarding(): Promise<boolean> {
	if (state.checked) {
		return state.needsOnboarding;
	}

	state.loading = true;

	try {
		// If onboarding was completed before, skip the check
		if (wasOnboardingCompleted()) {
			state.needsOnboarding = false;
			state.showWizard = false;
			state.checked = true;
			state.loading = false;
			return false;
		}

		const settings = await getSettings();

		// No key configured at all
		if (!settings.openai_key?.configured) {
			state.needsOnboarding = true;
			state.showWizard = true;
			state.checked = true;
			state.loading = false;
			return true;
		}

		// Key is configured, validate it
		const validation = await validateApiKey('openai', '__USE_STORED__');
		state.needsOnboarding = !validation.valid;
		state.showWizard = !validation.valid;
		state.checked = true;
		state.loading = false;
		return state.needsOnboarding;
	} catch {
		// On error, assume we need onboarding
		state.needsOnboarding = true;
		state.showWizard = true;
		state.checked = true;
		state.loading = false;
		return true;
	}
}

/**
 * Mark onboarding as complete.
 */
export function completeOnboarding(): void {
	state.needsOnboarding = false;
	state.showWizard = false;
	state.checked = true;
	try {
		localStorage.setItem(STORAGE_KEY, 'true');
	} catch {
		// Ignore storage errors
	}
}

/**
 * Reset the onboarding check (forces re-check on next call).
 */
export function resetOnboardingCheck(): void {
	state.checked = false;
	state.needsOnboarding = false;
	state.showWizard = false;
	try {
		localStorage.removeItem(STORAGE_KEY);
	} catch {
		// Ignore storage errors
	}
}

/**
 * Hide the wizard modal without marking complete.
 */
export function hideWizard(): void {
	state.showWizard = false;
}

/**
 * Get current onboarding state (reactive).
 */
export function getOnboardingState(): OnboardingState {
	return state;
}
