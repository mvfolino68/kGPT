"""
Kafka agent tools using the unified KafkaService.
These tools are bound to the agent's LLM to allow it to interact with the cluster.
"""

from langchain_core.tools import tool

from kgpt.services import get_kafka_service


@tool
def list_topics_tool() -> list[dict]:
    """
    List all Kafka topics in the connected cluster.
    Returns a list of topics with their partition counts and replication factors.
    Use this to see what data is available in the cluster.
    """
    service = get_kafka_service()
    topics = service.list_topics()
    # Convert Pydantic models to dicts for tool output
    return [t.model_dump() for t in topics]


@tool
def describe_topic_tool(topic_name: str) -> dict:
    """
    Get detailed information about a specific Kafka topic.
    Includes partition details (leaders, replicas, ISRs) and configuration overrides.

    Args:
        topic_name: The name of the topic to describe.
    """
    service = get_kafka_service()
    return service.describe_topic(topic_name)


@tool
def create_topic_tool(
    topic_name: str,
    num_partitions: int = 1,
    replication_factor: int = 1,
    cleanup_policy: str | None = None,
    retention_ms: int | None = None,
) -> dict:
    """
    Create a new Kafka topic.

    Args:
        topic_name: Unique name for the new topic.
        num_partitions: Number of partitions (default: 1).
        replication_factor: Number of replicas (default: 1).
        cleanup_policy: Optional config 'cleanup.policy' (e.g., 'delete' or 'compact').
        retention_ms: Optional config 'retention.ms' (milliseconds).
    """
    config = {}
    if cleanup_policy:
        config["cleanup.policy"] = cleanup_policy
    if retention_ms:
        config["retention.ms"] = str(retention_ms)

    service = get_kafka_service()
    return service.create_topic(
        topic_name=topic_name,
        num_partitions=num_partitions,
        replication_factor=replication_factor,
        config=config if config else None,
    )


@tool
def delete_topic_tool(topic_name: str) -> dict:
    """
    Delete a Kafka topic.
    Warning: This action is irreversible and deletes all data in the topic.

    Args:
        topic_name: Name of the topic to delete.
    """
    service = get_kafka_service()
    return service.delete_topic(topic_name)


@tool
def list_consumer_groups_tool() -> list[dict]:
    """
    List all consumer groups in the cluster.
    Returns group IDs and states.
    """
    service = get_kafka_service()
    groups = service.list_consumer_groups()
    return [g.model_dump() for g in groups]


@tool
def describe_consumer_group_tool(group_id: str) -> dict:
    """
    Get detailed info about a consumer group, including members and assignments.

    Args:
        group_id: The consumer group ID.
    """
    service = get_kafka_service()
    return service.describe_consumer_group(group_id)


@tool
def describe_cluster_tool() -> dict:
    """
    Get general cluster information: brokers, controller, and overall stats.
    Useful for checking cluster health and topology.
    """
    service = get_kafka_service()
    details = service.get_cluster_details()
    # Filter down for tool use - LLM doesn't need everything
    return {
        "connected": details["connected"],
        "name": details["name"],
        "cluster_id": details["cluster_id"],
        "broker_count": details["broker_count"],
        "topic_count": details["topic_count"],
        "total_partitions": details["total_partitions"],
        "under_replicated_count": details["under_replicated_count"],
        "controller_id": details["controller_id"],
        "brokers": [b.model_dump() for b in details["brokers"]],
    }


@tool
def get_kafka_logs_tool(lines: int = 50) -> list[str]:
    """
    Get recent debug logs from the Kafka service.
    Use this to diagnose connection issues or check the status of operations.

    Args:
        lines: Number of recent log lines to retrieve (default: 50).
    """
    service = get_kafka_service()
    return service.get_recent_logs(lines=lines)


def get_kafka_tools():
    """Get list of all Kafka tools."""
    return [
        list_topics_tool,
        describe_topic_tool,
        create_topic_tool,
        delete_topic_tool,
        list_consumer_groups_tool,
        describe_consumer_group_tool,
        describe_cluster_tool,
        get_kafka_logs_tool,
    ]
