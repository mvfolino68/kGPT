import { writable } from 'svelte/store';
import type { HealthResponse } from '$lib/api';
import { checkHealth } from '$lib/api';

export const health = writable<HealthResponse | null>(null);
export const healthError = writable<string | null>(null);

export async function refreshHealth() {
	try {
		const data = await checkHealth();
		health.set(data);
		healthError.set(null);
	} catch (e) {
		healthError.set(e instanceof Error ? e.message : 'Failed to check health');
		health.set(null);
	}
}
