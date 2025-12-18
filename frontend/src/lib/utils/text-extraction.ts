/**
 * Extract text content safely from any value (handles various LLM chunk formats)
 */
export function extractTextContent(value: unknown): string {
	if (value === null || value === undefined) return '';
	if (typeof value === 'string') return value;
	if (typeof value === 'number') return String(value);
	
	if (Array.isArray(value)) {
		return value.map(item => {
			if (typeof item === 'string') return item;
			if (typeof item === 'object' && item !== null) {
				if ('text' in item && typeof item.text === 'string') return item.text;
				if ('content' in item && typeof item.content === 'string') return item.content;
			}
			return '';
		}).join('');
	}
	
	if (typeof value === 'object') {
		const obj = value as Record<string, unknown>;
		if ('text' in obj && typeof obj.text === 'string') return obj.text;
		if ('content' in obj && typeof obj.content === 'string') return obj.content;
	}
	
	return '';
}
