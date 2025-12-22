<script lang="ts">
	import { Modal, Button, Icon } from '$lib/components';
	import { ConsumerGroupsPanel } from '$lib/components/cluster';
	import { pendingChatAction } from '$lib/stores/chat';
	import type { ConsumerGroupInfo } from '$lib/api';

	interface Props {
		isOpen: boolean;
		groups: ConsumerGroupInfo[];
		onClose: () => void;
		onGroupClick: (group: string) => void;
	}

	let { isOpen, groups, onClose, onGroupClick }: Props = $props();
</script>


<Modal {isOpen} {onClose} title="Consumer Groups" size="xl">
	<div class="flex justify-end mb-4">
		<Button
			variant="secondary"
			size="sm"
			onclick={() => {
				onClose();
				pendingChatAction.set({
					message: 'Analyze the status of consumer groups.',
					newSession: true
				});
			}}
		>
			<Icon name="sparkles" size="sm" />
			Analyze Groups
		</Button>
	</div>
	<ConsumerGroupsPanel {groups} {onGroupClick} />
</Modal>
