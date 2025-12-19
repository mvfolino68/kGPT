import type { AdminOperationResult, PartitionDetail } from '$lib/stores/chat';

export type { AdminOperationResult, PartitionDetail };

export interface TopicInfo {
	name: string;
	partitions?: number;
}

export interface GroupInfo {
	group_id: string;
	state?: string;
}

export interface BrokerInfo {
	id: number;
	host: string;
	port: number;
}

export interface OffsetInfo {
	topic: string;
	partition: number;
	offset: number;
}

export interface MemberInfo {
	client_id: string;
	host: string;
}

export interface CoordinatorInfo {
	host: string;
	port: number;
}

export interface ConfigValue {
	value: string;
	is_default: boolean;
	is_read_only: boolean;
}

export type ConfigEntry = string | ConfigValue;

export function formatConfigValue(value: ConfigEntry): string {
	if (typeof value === 'string') return value;
	return value.value;
}

export function isDefault(value: ConfigEntry): boolean {
	if (typeof value === 'string') return false;
	return value.is_default;
}

export function isPartitionDetailList(
	partitions: number | PartitionDetail[] | undefined
): partitions is PartitionDetail[] {
	return Array.isArray(partitions);
}

