"""Kafka cluster agent for retrieving live cluster information."""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from kgpt.agents.state import AgentState

if TYPE_CHECKING:
    from confluent_kafka.admin import AdminClient


class KafkaClusterContext:
    """Kafka cluster context retriever using confluent-kafka AdminClient."""

    def __init__(
        self,
        bootstrap_servers: str,
        security_protocol: str = "PLAINTEXT",
        sasl_mechanism: str | None = None,
        sasl_username: str | None = None,
        sasl_password: str | None = None,
    ):
        """Initialize the Kafka cluster context."""
        self.bootstrap_servers = bootstrap_servers
        self.config = {
            "bootstrap.servers": bootstrap_servers,
            "security.protocol": security_protocol,
        }

        if sasl_mechanism:
            self.config["sasl.mechanism"] = sasl_mechanism
        if sasl_username:
            self.config["sasl.username"] = sasl_username
        if sasl_password:
            self.config["sasl.password"] = sasl_password

        self._admin: AdminClient | None = None

    @property
    def admin(self):
        """Lazy-load the AdminClient."""
        if self._admin is None:
            from confluent_kafka.admin import AdminClient

            self._admin = AdminClient(self.config)
        return self._admin

    def get_cluster_metadata(self, timeout: float = 10.0) -> dict:
        """Get basic cluster metadata."""
        try:
            metadata = self.admin.list_topics(timeout=timeout)

            brokers = {}
            for broker_id, broker in metadata.brokers.items():
                brokers[broker_id] = {
                    "host": broker.host,
                    "port": broker.port,
                }

            topics = list(metadata.topics.keys())

            return {
                "cluster_id": metadata.cluster_id,
                "controller_id": metadata.controller_id,
                "broker_count": len(brokers),
                "brokers": brokers,
                "topic_count": len(topics),
                "topics": topics,
            }

        except Exception as e:
            logger.error(f"Error getting cluster metadata: {e}")
            raise

    def get_topic_details(self, topic_name: str, timeout: float = 10.0) -> dict:
        """Get detailed information about a specific topic."""
        try:
            metadata = self.admin.list_topics(topic=topic_name, timeout=timeout)

            if topic_name not in metadata.topics:
                return {"error": f"Topic '{topic_name}' not found"}

            topic = metadata.topics[topic_name]
            partitions = {}

            for partition_id, partition in topic.partitions.items():
                partitions[partition_id] = {
                    "leader": partition.leader,
                    "replicas": list(partition.replicas),
                    "isrs": list(partition.isrs),
                }

            return {
                "name": topic_name,
                "partition_count": len(partitions),
                "partitions": partitions,
            }

        except Exception as e:
            logger.error(f"Error getting topic details: {e}")
            raise

    def get_topic_config(self, topic_name: str, timeout: float = 10.0) -> dict:
        """Get configuration for a specific topic."""
        try:
            from confluent_kafka.admin import ConfigResource, ResourceType

            resource = ConfigResource(ResourceType.TOPIC, topic_name)
            futures = self.admin.describe_configs([resource])

            for _res, future in futures.items():
                config = future.result(timeout=timeout)
                return {
                    "topic": topic_name,
                    "configs": {
                        entry.name: {
                            "value": entry.value,
                            "is_default": entry.is_default,
                            "is_read_only": entry.is_read_only,
                        }
                        for entry in config.values()
                    },
                }

            return {"error": "No configuration returned"}

        except Exception as e:
            logger.error(f"Error getting topic config: {e}")
            raise

    def get_consumer_groups(self, timeout: float = 10.0) -> list[dict]:
        """Get list of consumer groups."""
        try:
            groups = self.admin.list_consumer_groups(timeout=timeout)
            valid_groups = groups.result(timeout=timeout).valid

            return [
                {
                    "group_id": g.group_id,
                    "is_simple": g.is_simple_consumer_group,
                    "state": str(g.state) if hasattr(g, "state") else "unknown",
                }
                for g in valid_groups
            ]

        except Exception as e:
            logger.error(f"Error getting consumer groups: {e}")
            raise

    def test_connection(self, timeout: float = 5.0) -> tuple[bool, str]:
        """Test connection to the cluster."""
        try:
            metadata = self.admin.list_topics(timeout=timeout)
            broker_count = len(metadata.brokers)
            topic_count = len(metadata.topics)
            return True, f"Connected: {broker_count} brokers, {topic_count} topics"
        except Exception as e:
            return False, str(e)

    # ========================================================================
    # Admin Operations
    # ========================================================================

    def delete_topic(self, topic_name: str, timeout: float = 30.0) -> dict:
        """Delete a topic from the cluster."""
        try:
            futures = self.admin.delete_topics([topic_name], operation_timeout=timeout)

            for topic, future in futures.items():
                try:
                    future.result(timeout=timeout)
                    logger.info(f"Successfully deleted topic: {topic}")
                    return {
                        "success": True,
                        "operation": "delete_topic",
                        "topic": topic_name,
                        "message": f"Topic '{topic_name}' has been deleted successfully.",
                    }
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Failed to delete topic {topic}: {error_msg}")
                    return {
                        "success": False,
                        "operation": "delete_topic",
                        "topic": topic_name,
                        "error": error_msg,
                    }

            return {
                "success": False,
                "operation": "delete_topic",
                "topic": topic_name,
                "error": "No result returned from delete operation",
            }

        except Exception as e:
            logger.error(f"Error deleting topic {topic_name}: {e}")
            return {
                "success": False,
                "operation": "delete_topic",
                "topic": topic_name,
                "error": str(e),
            }

    def create_topic(
        self,
        topic_name: str,
        num_partitions: int = 1,
        replication_factor: int = 1,
        config: dict | None = None,
        timeout: float = 30.0,
    ) -> dict:
        """Create a new topic in the cluster."""
        try:
            from confluent_kafka.admin import NewTopic

            new_topic = NewTopic(
                topic_name,
                num_partitions=num_partitions,
                replication_factor=replication_factor,
                config=config or {},
            )

            futures = self.admin.create_topics([new_topic], operation_timeout=timeout)

            for topic, future in futures.items():
                try:
                    future.result(timeout=timeout)
                    logger.info(f"Successfully created topic: {topic}")
                    return {
                        "success": True,
                        "operation": "create_topic",
                        "topic": topic_name,
                        "partitions": num_partitions,
                        "replication_factor": replication_factor,
                        "message": f"Topic '{topic_name}' created with {num_partitions} partition(s) and replication factor {replication_factor}.",
                    }
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Failed to create topic {topic}: {error_msg}")
                    return {
                        "success": False,
                        "operation": "create_topic",
                        "topic": topic_name,
                        "error": error_msg,
                    }

            return {
                "success": False,
                "operation": "create_topic",
                "topic": topic_name,
                "error": "No result returned from create operation",
            }

        except Exception as e:
            logger.error(f"Error creating topic {topic_name}: {e}")
            return {
                "success": False,
                "operation": "create_topic",
                "topic": topic_name,
                "error": str(e),
            }

    def alter_topic_config(
        self,
        topic_name: str,
        config_updates: dict[str, str],
        timeout: float = 30.0,
    ) -> dict:
        """Alter configuration for a topic."""
        try:
            from confluent_kafka.admin import ConfigResource, ResourceType

            resource = ConfigResource(ResourceType.TOPIC, topic_name)

            # Set each config value
            for key, value in config_updates.items():
                resource.set_config(key, value)

            futures = self.admin.alter_configs([resource])

            for res, future in futures.items():
                try:
                    future.result(timeout=timeout)
                    logger.info(f"Successfully altered config for topic: {topic_name}")
                    return {
                        "success": True,
                        "operation": "alter_topic_config",
                        "topic": topic_name,
                        "config_updates": config_updates,
                        "message": f"Configuration for topic '{topic_name}' has been updated: {config_updates}",
                    }
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Failed to alter config for {topic_name}: {error_msg}")
                    return {
                        "success": False,
                        "operation": "alter_topic_config",
                        "topic": topic_name,
                        "error": error_msg,
                    }

            return {
                "success": False,
                "operation": "alter_topic_config",
                "topic": topic_name,
                "error": "No result returned from alter operation",
            }

        except Exception as e:
            logger.error(f"Error altering config for topic {topic_name}: {e}")
            return {
                "success": False,
                "operation": "alter_topic_config",
                "topic": topic_name,
                "error": str(e),
            }

    def delete_consumer_group(self, group_id: str, timeout: float = 30.0) -> dict:
        """Delete a consumer group."""
        try:
            futures = self.admin.delete_consumer_groups([group_id])

            for group, future in futures.items():
                try:
                    future.result(timeout=timeout)
                    logger.info(f"Successfully deleted consumer group: {group}")
                    return {
                        "success": True,
                        "operation": "delete_consumer_group",
                        "group_id": group_id,
                        "message": f"Consumer group '{group_id}' has been deleted successfully.",
                    }
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Failed to delete consumer group {group}: {error_msg}")
                    return {
                        "success": False,
                        "operation": "delete_consumer_group",
                        "group_id": group_id,
                        "error": error_msg,
                    }

            return {
                "success": False,
                "operation": "delete_consumer_group",
                "group_id": group_id,
                "error": "No result returned from delete operation",
            }

        except Exception as e:
            logger.error(f"Error deleting consumer group {group_id}: {e}")
            return {
                "success": False,
                "operation": "delete_consumer_group",
                "group_id": group_id,
                "error": str(e),
            }

    def describe_consumer_group(self, group_id: str, timeout: float = 10.0) -> dict:
        """Get detailed information about a consumer group."""
        try:
            futures = self.admin.describe_consumer_groups([group_id])

            for group, future in futures.items():
                try:
                    result = future.result(timeout=timeout)
                    members = []
                    for member in result.members:
                        member_info = {
                            "member_id": member.member_id,
                            "client_id": member.client_id,
                            "host": member.host,
                        }
                        if hasattr(member, "assignment") and member.assignment:
                            member_info["assignments"] = [
                                {"topic": tp.topic, "partition": tp.partition}
                                for tp in member.assignment.topic_partitions
                            ]
                        members.append(member_info)

                    return {
                        "group_id": result.group_id,
                        "state": str(result.state),
                        "protocol_type": result.protocol_type,
                        "protocol": result.protocol,
                        "coordinator": {
                            "id": result.coordinator.id if result.coordinator else None,
                            "host": result.coordinator.host if result.coordinator else None,
                            "port": result.coordinator.port if result.coordinator else None,
                        },
                        "members": members,
                    }
                except Exception as e:
                    logger.error(f"Failed to describe consumer group {group}: {e}")
                    return {"error": str(e)}

            return {"error": "No result returned"}

        except Exception as e:
            logger.error(f"Error describing consumer group {group_id}: {e}")
            return {"error": str(e)}

    def add_partitions(
        self,
        topic_name: str,
        new_total_partitions: int,
        timeout: float = 30.0,
    ) -> dict:
        """Add partitions to a topic."""
        try:
            from confluent_kafka.admin import NewPartitions

            new_parts = NewPartitions(topic_name, new_total_partitions)
            futures = self.admin.create_partitions([new_parts], operation_timeout=timeout)

            for topic, future in futures.items():
                try:
                    future.result(timeout=timeout)
                    logger.info(f"Successfully added partitions to topic: {topic}")
                    return {
                        "success": True,
                        "operation": "add_partitions",
                        "topic": topic_name,
                        "new_total_partitions": new_total_partitions,
                        "message": f"Topic '{topic_name}' now has {new_total_partitions} partitions.",
                    }
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Failed to add partitions to {topic}: {error_msg}")
                    return {
                        "success": False,
                        "operation": "add_partitions",
                        "topic": topic_name,
                        "error": error_msg,
                    }

            return {
                "success": False,
                "operation": "add_partitions",
                "topic": topic_name,
                "error": "No result returned from operation",
            }

        except Exception as e:
            logger.error(f"Error adding partitions to topic {topic_name}: {e}")
            return {
                "success": False,
                "operation": "add_partitions",
                "topic": topic_name,
                "error": str(e),
            }

    def describe_topic(self, topic_name: str, timeout: float = 10.0) -> dict:
        """Get comprehensive information about a topic including details and configuration."""
        try:
            # Get topic details (partitions, replicas, ISRs)
            details = self.get_topic_details(topic_name, timeout=timeout)
            if "error" in details:
                return {
                    "success": False,
                    "operation": "describe_topic",
                    "topic": topic_name,
                    "error": details["error"],
                }

            # Get topic configuration
            config_result = self.get_topic_config(topic_name, timeout=timeout)
            configs = config_result.get("configs", {}) if "error" not in config_result else {}

            # Format the response
            partitions_info = []
            for partition_id, partition_data in details.get("partitions", {}).items():
                partitions_info.append(
                    {
                        "partition": partition_id,
                        "leader": partition_data.get("leader"),
                        "replicas": partition_data.get("replicas", []),
                        "isrs": partition_data.get("isrs", []),
                    }
                )

            # Extract important config values
            important_configs = {}
            for key, value_info in configs.items():
                if not value_info.get("is_read_only", False):
                    important_configs[key] = value_info.get("value")

            logger.info(f"Successfully described topic: {topic_name}")
            return {
                "success": True,
                "operation": "describe_topic",
                "topic": topic_name,
                "partition_count": details.get("partition_count", 0),
                "partitions": partitions_info,
                "configuration": important_configs,
                "all_configs": configs,
                "message": f"Topic '{topic_name}' has {details.get('partition_count', 0)} partition(s).",
            }

        except Exception as e:
            logger.error(f"Error describing topic {topic_name}: {e}")
            return {
                "success": False,
                "operation": "describe_topic",
                "topic": topic_name,
                "error": str(e),
            }


# Global cluster context (set via UI)
_cluster_context: KafkaClusterContext | None = None


def set_cluster_context(context: KafkaClusterContext | None):
    """Set the global cluster context."""
    global _cluster_context
    _cluster_context = context


def get_cluster_context() -> KafkaClusterContext | None:
    """Get the global cluster context."""
    return _cluster_context


async def kafka_node(state: AgentState) -> dict:
    """
    Kafka agent node that retrieves cluster context.

    Fetches relevant cluster information based on the question.
    """
    logger.info("Kafka agent retrieving cluster context...")

    context = get_cluster_context()

    if context is None:
        logger.warning("No Kafka cluster configured")
        return {
            "cluster_context": None,
            "error": "No Kafka cluster connected. Configure a cluster in the Cluster page.",
        }

    try:
        # Get basic cluster metadata
        cluster_info = context.get_cluster_metadata()

        # Check if the question mentions specific topics
        question_lower = state["question"].lower()
        topic_details = {}

        for topic in cluster_info.get("topics", [])[:5]:  # Limit to first 5
            if topic.lower() in question_lower:
                try:
                    details = context.get_topic_details(topic)
                    config = context.get_topic_config(topic)
                    topic_details[topic] = {**details, "config": config.get("configs", {})}
                except Exception as e:
                    logger.warning(f"Could not get details for topic {topic}: {e}")

        # Get consumer groups if relevant
        consumer_groups = []
        if any(term in question_lower for term in ["consumer", "group", "lag", "offset"]):
            try:
                consumer_groups = context.get_consumer_groups()
            except Exception as e:
                logger.warning(f"Could not get consumer groups: {e}")

        cluster_context = {
            **cluster_info,
            "topic_details": topic_details if topic_details else None,
            "consumer_groups": consumer_groups if consumer_groups else None,
        }

        logger.info(f"Kafka agent retrieved context: {len(cluster_info.get('topics', []))} topics")

        return {"cluster_context": cluster_context}

    except Exception as e:
        logger.error(f"Kafka agent error: {e}")
        return {
            "cluster_context": None,
            "error": f"Failed to retrieve cluster information: {str(e)}",
        }
