"""
Unified Kafka Service handling all cluster interactions.
Replaces the legacy KafkaClusterContext and AdminNode logic.
"""

import os
from datetime import datetime
from typing import Any

from confluent_kafka.admin import (
    AdminClient,
    ConfigResource,
    NewPartitions,
    NewTopic,
    ResourceType,
)
from loguru import logger

# Additional file-based logging for debugging when we can't see the console
KAFKA_DEBUG_LOG = "kafka_debug.log"
if not os.path.exists(KAFKA_DEBUG_LOG):
    with open(KAFKA_DEBUG_LOG, "w") as f:
        f.write("Kafka Debug Log initialized\n")


def debug_log(msg):
    with open(KAFKA_DEBUG_LOG, "a") as f:
        f.write(f"{datetime.now()} | {msg}\n")
    logger.debug(msg)


from kgpt.api.schemas import (
    BrokerInfo,
    ClusterInfo,
    ConsumerGroupInfo,
    PartitionDetail,
    TopicInfo,
)


class KafkaService:
    """
    Service layer for Kafka operations.
    Can be used by both the FastAPI backend and Agent Tools.
    """

    def __init__(self, config: dict | None = None):
        """
        Initialize with connection config.
        If config is None, operations will fail until set_config is called.
        """
        self.config = config
        self._admin_client: AdminClient | None = None

    def set_config(self, config: dict):
        """Update connection configuration."""
        self.config = config
        self._admin_client = None  # Reset client to force reconnection

    def _get_admin_client(self) -> AdminClient:
        """Get or create a cached AdminClient instance."""
        if self._admin_client:
            return self._admin_client

        if not self.config:
            raise ValueError("Kafka configuration not set. Please connect to a cluster first.")

        # Build confluent_kafka configuration
        bootstrap_servers = self.config.get("bootstrap_servers")
        logger.info(f"Creating AdminClient with bootstrap.servers: {bootstrap_servers}")
        conf = {"bootstrap.servers": bootstrap_servers}

        # Add security config if present
        security_protocol = self.config.get("security_protocol")
        if security_protocol and security_protocol != "PLAINTEXT":
            conf["security.protocol"] = security_protocol

            sasl_mechanism = self.config.get("sasl_mechanism")
            sasl_username = self.config.get("sasl_username")
            sasl_password = self.config.get("sasl_password")

            if sasl_mechanism:
                conf["sasl.mechanism"] = sasl_mechanism
            if sasl_username:
                conf["sasl.username"] = sasl_username
            if sasl_password:
                conf["sasl.password"] = sasl_password

        # Create new client
        try:
            self._admin_client = AdminClient(conf)
            return self._admin_client
        except Exception as e:
            logger.error(f"Failed to create AdminClient: {e}")
            raise ConnectionError(f"Failed to create Kafka client: {e}")

    # ========================================================================
    # Connection / Metadata
    # ========================================================================

    def test_connection(self) -> ClusterInfo:
        """Test connection and return basic cluster info."""
        client = self._get_admin_client()
        try:
            # Metadata call proves connection
            metadata = client.list_topics(timeout=10)

            return ClusterInfo(
                name=self.config.get("name", "Unknown"),
                bootstrap_servers=self.config.get("bootstrap_servers", ""),
                connected=True,
                brokers=len(metadata.brokers),
                topics=[t for t in metadata.topics if not t.startswith("_")],
                cluster_id=metadata.cluster_id,
            )
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            # Identify specific errors if possible, or re-raise
            raise ConnectionError(f"Could not connect to cluster: {e}")

    def get_cluster_details(self) -> dict[str, Any]:
        """
        Get comprehensive details for dashboard/agent context.
        Returns a dict structure matching ClusterDetailsResponse fields.
        """
        client = self._get_admin_client()
        metadata = client.list_topics(timeout=10)

        # First pass: Calculate partition and leader counts per broker
        broker_partition_counts: dict[int, int] = {}
        broker_leader_counts: dict[int, int] = {}

        for name, topic in metadata.topics.items():
            if name.startswith("_"):
                continue  # Skip internal topics for broker stats

            for partition in topic.partitions.values():
                # Count partitions per broker (replicas)
                for replica_id in partition.replicas:
                    broker_partition_counts[replica_id] = (
                        broker_partition_counts.get(replica_id, 0) + 1
                    )

                # Count leader partitions per broker
                if partition.leader is not None and partition.leader >= 0:
                    broker_leader_counts[partition.leader] = (
                        broker_leader_counts.get(partition.leader, 0) + 1
                    )

        # Process Brokers with partition/leader counts
        brokers = []
        broker_ids = sorted(metadata.brokers.keys())
        for bid in broker_ids:
            b = metadata.brokers[bid]
            brokers.append(
                BrokerInfo(
                    id=int(bid),
                    host=b.host,
                    port=b.port,
                    is_controller=(int(bid) == int(metadata.controller_id)),
                    partition_count=broker_partition_counts.get(int(bid), 0),
                    leader_count=broker_leader_counts.get(int(bid), 0),
                )
            )

        # Process Topics
        topics = []
        total_partitions = 0
        under_replicated_count = 0

        for name, topic in metadata.topics.items():
            if name.startswith("_"):
                continue  # Skip internal topics usually? Or keep them marked

            partitions_list = list(topic.partitions.values())
            p_count = len(partitions_list)
            total_partitions += p_count

            # Check replication (take first partition as sample)
            rf = len(partitions_list[0].replicas) if partitions_list else 0

            # Check URP
            is_under_replicated = False
            for p in partitions_list:
                if len(p.isrs) < len(p.replicas):
                    is_under_replicated = True
                    break

            if is_under_replicated:
                under_replicated_count += 1

            topics.append(
                TopicInfo(
                    name=name,
                    partition_count=p_count,
                    replication_factor=rf,
                    is_internal=name.startswith("_"),
                    under_replicated=is_under_replicated,
                )
            )

        # Process Consumer Groups (list only)
        # Force a fresh client for consumer groups - the cached client may have stale connections
        groups = []
        try:
            # Refresh the client to ensure consumer groups are fetched properly
            debug_log("Refreshing AdminClient for consumer groups list...")
            self._admin_client = None
            fresh_client = self._get_admin_client()
            debug_log(f"Using servers: {self.config.get('bootstrap_servers')}")
            group_future = fresh_client.list_consumer_groups()
            group_results = group_future.result(timeout=10)
            debug_log(
                f"Consumer groups API returned: valid={len(group_results.valid)}, errors={group_results.errors}"
            )
            group_ids = [g.group_id for g in group_results.valid]
            description_futures = {}
            if group_ids:
                description_futures = fresh_client.describe_consumer_groups(group_ids)

            for g in group_results.valid:
                debug_log(f"Found consumer group: {g.group_id} state={g.state}")

                try:
                    # Try to get full details
                    g_desc = description_futures[g.group_id].result()
                    member_count = len(g_desc.members)
                    group_topics = set()
                    for m in g_desc.members:
                        if m.assignment:
                            for tp in m.assignment.topic_partitions:
                                group_topics.add(tp.topic)

                    groups.append(
                        ConsumerGroupInfo(
                            group_id=g.group_id,
                            state=str(g.state),
                            protocol_type=getattr(g_desc, "protocol_type", None),
                            member_count=member_count,
                            coordinator_id=g_desc.coordinator.id if g_desc.coordinator else None,
                            topics=list(group_topics),
                        )
                    )
                except Exception as e:
                    debug_log(f"Fallback for group {g.group_id}: {e}")
                    # Fallback to basic info if describe fails
                    groups.append(
                        ConsumerGroupInfo(
                            group_id=g.group_id,
                            state=str(g.state),
                            protocol_type=getattr(g, "protocol_type", None),
                        )
                    )
        except Exception as e:
            import traceback

            debug_log(f"Failed to list consumer groups: {e}")
            debug_log(f"Traceback: {traceback.format_exc()}")
            logger.warning(f"Failed to list consumer groups: {e}")
            logger.warning(f"Traceback: {traceback.format_exc()}")

        return {
            "connected": True,
            "name": self.config.get("name"),
            "cluster_id": metadata.cluster_id,
            "controller_id": int(metadata.controller_id),
            "brokers": brokers,
            "broker_count": len(brokers),
            "topics": sorted(topics, key=lambda x: x.name),
            "topic_count": len(topics),
            "total_partitions": total_partitions,
            "under_replicated_count": under_replicated_count,
            "consumer_groups": groups,
            "consumer_group_count": len(groups),
        }

    # ========================================================================
    # Topic Operations
    # ========================================================================

    def list_topics(self) -> list[TopicInfo]:
        """List all topics with basic info."""
        details = self.get_cluster_details()
        return details["topics"]

    def describe_topic(self, topic_name: str) -> dict[str, Any]:
        """
        Get detailed topic info: partitions, config, etc.
        Returns dict suitable for tool output or API response.
        """
        client = self._get_admin_client()

        # 1. Metadata for partitions
        md = client.list_topics(topic=topic_name, timeout=10)
        if topic_name not in md.topics:
            raise ValueError(f"Topic '{topic_name}' not found")

        t_md = md.topics[topic_name]
        partitions_data = []
        for pid, p in t_md.partitions.items():
            partitions_data.append(
                PartitionDetail(partition=pid, leader=p.leader, replicas=p.replicas, isrs=p.isrs)
            )

        # 2. Config
        resource = ConfigResource(ResourceType.TOPIC, topic_name)
        futures = client.describe_configs([resource])
        config_result = futures[resource].result()

        configs = {}
        for entry in config_result.values():
            # Filter for non-default or include all?
            # Tool-use usually appreciates concise output, but let's give full map
            # simplified for JSON
            configs[entry.name] = entry.value

        return {
            "name": topic_name,
            "partition_count": len(partitions_data),
            "replication_factor": len(partitions_data[0].replicas) if partitions_data else 0,
            "partitions": [p.model_dump() for p in partitions_data],
            "config": configs,
            "is_internal": topic_name.startswith("_"),
        }

    def create_topic(
        self,
        topic_name: str,
        num_partitions: int = 1,
        replication_factor: int = 1,
        config: dict | None = None,
    ) -> dict[str, Any]:
        """Create a new topic."""
        client = self._get_admin_client()

        topic = NewTopic(
            topic_name,
            num_partitions=num_partitions,
            replication_factor=replication_factor,
            config=config or {},
        )

        futures = client.create_topics([topic])
        try:
            futures[topic_name].result()  # Wait for completion
            return {
                "success": True,
                "message": f"Topic '{topic_name}' created successfully.",
                "topic": topic_name,
                "partitions": num_partitions,
                "replication_factor": replication_factor,
            }
        except Exception as e:
            logger.error(f"Failed to create topic {topic_name}: {e}")
            raise RuntimeError(f"Failed to create topic: {e}")

    def delete_topic(self, topic_name: str) -> dict[str, Any]:
        """Delete a topic."""
        client = self._get_admin_client()

        futures = client.delete_topics([topic_name])
        try:
            futures[topic_name].result()
            return {
                "success": True,
                "message": f"Topic '{topic_name}' deleted successfully.",
                "topic": topic_name,
            }
        except Exception as e:
            raise RuntimeError(f"Failed to delete topic: {e}")

    def add_partitions(self, topic_name: str, new_total_count: int) -> dict[str, Any]:
        """Increase partition count for a topic."""
        client = self._get_admin_client()

        new_parts = NewPartitions(topic_name, new_total_count)
        futures = client.create_partitions([new_parts])
        try:
            futures[topic_name].result()
            return {
                "success": True,
                "message": f"Partitions for '{topic_name}' increased to {new_total_count}.",
                "topic": topic_name,
                "total_partitions": new_total_count,
            }
        except Exception as e:
            raise RuntimeError(f"Failed to add partitions: {e}")

    def alter_topic_config(self, topic_name: str, config_updates: dict[str, str]) -> dict[str, Any]:
        """Update configuration for a topic."""
        client = self._get_admin_client()

        resource = ConfigResource(ResourceType.TOPIC, topic_name)
        for k, v in config_updates.items():
            resource.set_config(k, v)

        futures = client.alter_configs([resource])
        try:
            futures[resource].result()
            return {
                "success": True,
                "message": f"Config updated for topic '{topic_name}'.",
                "updates": config_updates,
            }
        except Exception as e:
            raise RuntimeError(f"Failed to alter config: {e}")

    # ========================================================================
    # Consumer Group Operations
    # ========================================================================

    def list_consumer_groups(self) -> list[ConsumerGroupInfo]:
        """List all consumer groups with full details."""
        client = self._get_admin_client()
        group_future = client.list_consumer_groups()
        group_results = group_future.result(timeout=10)

        if not group_results.valid:
            return []

        # Describe all groups to get member counts and topics
        group_ids = [g.group_id for g in group_results.valid]
        description_futures = client.describe_consumer_groups(group_ids)

        valid_groups = []
        for g in group_results.valid:
            try:
                g_desc = description_futures[g.group_id].result()
                member_count = len(g_desc.members)
                group_topics = set()
                for m in g_desc.members:
                    if m.assignment:
                        for tp in m.assignment.topic_partitions:
                            group_topics.add(tp.topic)

                valid_groups.append(
                    ConsumerGroupInfo(
                        group_id=g.group_id,
                        state=str(g.state),
                        protocol_type=getattr(g_desc, "protocol_type", None),
                        member_count=member_count,
                        coordinator_id=g_desc.coordinator.id if g_desc.coordinator else None,
                        topics=list(group_topics),
                    )
                )
            except Exception:
                # Fallback to basic info if describe fails
                valid_groups.append(
                    ConsumerGroupInfo(
                        group_id=g.group_id,
                        state=str(g.state),
                        protocol_type=getattr(g, "protocol_type", None),
                    )
                )
        return valid_groups

    def describe_consumer_group(self, group_id: str) -> dict[str, Any]:
        """Get detailed consumer group info."""
        client = self._get_admin_client()

        futures = client.describe_consumer_groups([group_id])
        try:
            g = futures[group_id].result()

            members = []
            assigned_topics = set()
            for m in g.members:
                # assignment
                if m.assignment:
                    for tp in m.assignment.topic_partitions:
                        assigned_topics.add(tp.topic)

                members.append(
                    {
                        "member_id": m.member_id,
                        "client_id": m.client_id,
                        "host": m.host,
                        "assignment_count": len(m.assignment.topic_partitions)
                        if m.assignment
                        else 0,
                    }
                )

            return {
                "group_id": g.group_id,
                "state": str(g.state),
                "protocol_type": getattr(g, "protocol_type", None),
                "coordinator": {"id": g.coordinator.id, "host": g.coordinator.host}
                if g.coordinator
                else None,
                "members": members,
                "assigned_topics": list(assigned_topics),
                "member_count": len(members),
            }
        except Exception as e:
            raise RuntimeError(f"Failed to describe group: {e}")

    def delete_consumer_group(self, group_id: str) -> dict[str, Any]:
        """Delete a consumer group."""
        client = self._get_admin_client()

        futures = client.delete_consumer_groups([group_id])
        try:
            futures[group_id].result()
            return {
                "success": True,
                "message": f"Consumer group '{group_id}' deleted successfully.",
                "group_id": group_id,
            }
        except Exception as e:
            raise RuntimeError(f"Failed to delete consumer group: {e}")

    # ========================================================================
    # Broker Operations
    # ========================================================================

    def describe_broker_config(self, broker_id: int) -> dict[str, Any]:
        """Get configuration for a specific broker."""
        client = self._get_admin_client()
        resource = ConfigResource(ResourceType.BROKER, str(broker_id))
        futures = client.describe_configs([resource])

        try:
            config_result = futures[resource].result()
            configs = {}
            for entry in config_result.values():
                configs[entry.name] = entry.value
            return {"broker_id": broker_id, "config": configs}
        except Exception as e:
            raise RuntimeError(f"Failed to describe broker config: {e}")


# Global instance management (replaces the old set_cluster_context)
_kafka_service: KafkaService | None = None


def get_kafka_service() -> KafkaService:
    global _kafka_service
    if _kafka_service is None:
        _kafka_service = KafkaService()
    return _kafka_service
