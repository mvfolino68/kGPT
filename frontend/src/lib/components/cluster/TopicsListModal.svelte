<script lang="ts">
	import { Modal, Button, Icon } from '$lib/components';
	import { TopicsPanel } from '$lib/components/cluster';
	import { pendingChatAction } from '$lib/stores/chat';
	import type { TopicInfo } from '$lib/api';

	interface Props {
		isOpen: boolean;
		topics: TopicInfo[];
		onClose: () => void;
		onTopicClick: (topic: string) => void;
	}

	let { isOpen, topics, onClose, onTopicClick }: Props = $props();
</script>


<Modal {isOpen} {onClose} title="Topics" size="xl">
	<div class="flex justify-end mb-4">
		<Button
			variant="secondary"
			size="sm"
			onclick={() => {
				onClose();
				pendingChatAction.set({
					message: 'Analyze the current list of topics in the cluster.',
					newSession: true
				});
			}}
		>
			<Icon name="sparkles" size="sm" />
			Analyze Topics
		</Button>
	</div>
	<TopicsPanel {topics} {onTopicClick} />
</Modal>
