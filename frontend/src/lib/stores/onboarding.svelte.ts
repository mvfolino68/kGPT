/**
 * Onboarding state management.
 * Checks if the user needs to complete onboarding (no valid API key configured).
 */

import { getSettings, validateApiKey } from '$lib/api';

interface OnboardingState {
	checked: boolean;
	needsOnboarding: boolean;
	loading: boolean;
}

let state = $state<OnboardingState>({
	checked: false,
	needsOnboarding: false,
	loading: false
});

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
		const settings = await getSettings();

		// No key configured at all
		if (!settings.openai_key?.configured) {
			state.needsOnboarding = true;
			state.checked = true;
			state.loading = false;
			return true;
		}

		// Key is configured, validate it
		const validation = await validateApiKey('openai', '__USE_STORED__');
		state.needsOnboarding = !validation.valid;
		state.checked = true;
		state.loading = false;
		return state.needsOnboarding;
	} catch {
		// On error, assume we need onboarding
		state.needsOnboarding = true;
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
	state.checked = true;
}

/**
 * Reset the onboarding check (forces re-check on next call).
 */
export function resetOnboardingCheck(): void {
	state.checked = false;
	state.needsOnboarding = false;
}

/**
 * Get current onboarding state (reactive).
 */
export function getOnboardingState(): OnboardingState {
	return state;
}
