<script lang="ts">
	import { Button, Input, Select, SectionHeader, InnerCard } from '$lib/components/ui';
	import { FormField } from '$lib/components/settings';

	interface Props {
		name: string;
		bootstrap: string;
		protocol: string;
		connecting: boolean;
		onnamechange: (value: string) => void;
		onbootstrapchange: (value: string) => void;
		onprotocolchange: (value: string) => void;
		onconnect: () => void;
		oncancel: () => void;
	}

	let {
		name,
		bootstrap,
		protocol,
		connecting,
		onnamechange,
		onbootstrapchange,
		onprotocolchange,
		onconnect,
		oncancel
	}: Props = $props();

	const protocolOptions = [
		{ value: 'PLAINTEXT', label: 'PLAINTEXT' },
		{ value: 'SSL', label: 'SSL' },
		{ value: 'SASL_PLAINTEXT', label: 'SASL_PLAINTEXT' },
		{ value: 'SASL_SSL', label: 'SASL_SSL' }
	];

	// Local state for binding
	let nameValue = $state(name);
	let bootstrapValue = $state(bootstrap);
	let protocolValue = $state(protocol);

	$effect(() => { nameValue = name; });
	$effect(() => { bootstrapValue = bootstrap; });
	$effect(() => { protocolValue = protocol; });
</script>

<InnerCard padding="md">
	<SectionHeader spacing="md">New Connection</SectionHeader>
	<form onsubmit={(e) => { e.preventDefault(); onconnect(); }} class="space-y-4">
		<div class="grid grid-cols-2 gap-3">
			<FormField label="Name" id="cluster-name">
				<Input
					id="cluster-name"
					type="text"
					bind:value={nameValue}
					oninput={(e) => onnamechange(e.currentTarget.value)}
					placeholder="my-cluster"
				/>
			</FormField>
			<FormField label="Protocol" id="cluster-protocol">
				<Select
					id="cluster-protocol"
					bind:value={protocolValue}
					options={protocolOptions}
					onchange={() => onprotocolchange(protocolValue)}
				/>
			</FormField>
		</div>
		<FormField label="Bootstrap Servers" id="cluster-bootstrap">
			<Input
				id="cluster-bootstrap"
				type="text"
				bind:value={bootstrapValue}
				oninput={(e) => onbootstrapchange(e.currentTarget.value)}
				placeholder="localhost:9092"
			/>
		</FormField>
		<div class="flex gap-2 justify-end pt-2">
			<Button type="button" variant="ghost" onclick={oncancel}>
				Cancel
			</Button>
			<Button
				type="submit"
				variant="primary"
				disabled={connecting || !nameValue.trim() || !bootstrapValue.trim()}
				loading={connecting}
			>
				Connect
			</Button>
		</div>
	</form>
</InnerCard>
