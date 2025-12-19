<script lang="ts">
	import { goto } from '$app/navigation';
	import { Button, Card, Icon } from '$lib/components/ui';
</script>

<Card
	class="bg-primary/10 ring-1 ring-primary/25"
	padding="lg"
>
	<div class="text-center">
		<h3 class="text-lg font-semibold text-text mb-2">See it in action</h3>
		<p class="text-sm text-text-secondary mb-4">
			Watch the agent pipeline process your queries in real-time with the Activity sidebar.
		</p>
		<div class="flex justify-center">
			<Button variant="primary" onclick={() => goto('/')}>
				<Icon name="message" size="sm" />
				Start chatting
			</Button>
		</div>
	</div>
</Card>
