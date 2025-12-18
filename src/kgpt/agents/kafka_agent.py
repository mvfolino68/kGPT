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
