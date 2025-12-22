<script lang="ts">
	import { Modal, Input, Button, StatusMessage, Icon } from '$lib/components';
	import { executeAdminOperation } from '$lib/api';
	import { pendingChatAction } from '$lib/stores/chat';

	interface Props {
		isOpen: boolean;
		onClose: () => void;
		onSuccess: () => void;
	}

	let { isOpen, onClose, onSuccess }: Props = $props();

	let topicName = $state('');
	let partitions = $state(1);
	let replicationFactor = $state(1);
	let loading = $state(false);
	let error = $state<string | null>(null);

	async function handleSubmit() {
		loading = true;
		error = null;
		try {
			const result = await executeAdminOperation({
				operation: 'create_topic',
				params: {
					topic: topicName,
					partitions,
					replication_factor: replicationFactor
				}
			});

			if (result.success) {
				onSuccess();
				resetForm();
				onClose();
			} else {
				error = result.error || 'Failed to create topic';
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'An error occurred';
		} finally {
			loading = false;
		}
	}

	function resetForm() {
		topicName = '';
		partitions = 1;
		replicationFactor = 1;
		error = null;
	}
</script>

<Modal {isOpen} {onClose} title="Create New Topic">
	<div class="mb-4 flex justify-end">
		<Button
			variant="ghost"
			size="sm"
			class="text-primary hover:text-primary-hover"
			onclick={() => {
				onClose();
				pendingChatAction.set({
					message: 'I need help configuring a new Kafka topic. What are the best practices for partitions and replication?',
					newSession: true
				});
			}}
		>
			<Icon name="sparkles" size="sm" />
			Ask AI for Config Help
		</Button>
	</div>
	<form
		onsubmit={(e) => {
			e.preventDefault();
			handleSubmit();
		}}
		class="space-y-4"
	>
		{#if error}
			<StatusMessage variant="error" message={error} />
		{/if}

		<div>
			<label for="topic-name" class="label block mb-1.5">Topic Name</label>
			<Input
				id="topic-name"
				bind:value={topicName}
				placeholder="my-topic"
				required
				disabled={loading}
			/>
		</div>

		<div class="grid grid-cols-2 gap-4">
			<div>
				<label for="partitions" class="label block mb-1.5">Partitions</label>
				<Input
					id="partitions"
					type="number"
					bind:value={partitions}
					min="1"
					required
					disabled={loading}
				/>
			</div>
			<div>
				<label for="replication" class="label block mb-1.5">Replication Factor</label>
				<Input
					id="replication"
					type="number"
					bind:value={replicationFactor}
					min="1"
					required
					disabled={loading}
				/>
			</div>
		</div>

		<div class="flex justify-end gap-3 pt-2">
			<Button type="button" variant="ghost" onclick={onClose} disabled={loading}>
				Cancel
			</Button>
			<Button
				type="submit"
				variant="primary"
				loading={loading}
				disabled={!topicName.trim()}
			>
				Create Topic
			</Button>
		</div>
	</form>
</Modal>
