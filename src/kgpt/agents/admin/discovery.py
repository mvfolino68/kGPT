"""Operations discovery module for dynamic operation listing and suggestions."""

from kgpt.agents.kafka_agent import get_cluster_context

from .operations import (
    KAFKA_OPERATIONS,
    KafkaOperation,
    OperationType,
    get_all_operations,
    get_operations_by_category,
)


def get_operations_summary() -> dict:
    """
    Get a summary of all available operations grouped by category.

    Returns a structured dict suitable for API responses and help messages.
    """
    operations = get_all_operations()
    by_category = get_operations_by_category()

    # Count by type
    read_count = sum(1 for op in operations if op.operation_type == OperationType.READ)
    write_count = sum(1 for op in operations if op.operation_type == OperationType.WRITE)
    destructive_count = sum(
        1 for op in operations if op.operation_type == OperationType.DESTRUCTIVE
    )

    return {
        "total_operations": len(operations),
        "read_operations": read_count,
        "write_operations": write_count,
        "destructive_operations": destructive_count,
        "categories": list(by_category.keys()),
    }


def operation_to_dict(op: KafkaOperation) -> dict:
    """Convert a KafkaOperation to a serializable dict."""
    return {
        "id": op.id,
        "name": op.name,
        "description": op.description,
        "category": op.category,
        "operation_type": op.operation_type.value,
        "icon": op.icon,
        "params": [
            {
                "name": p.name,
                "label": p.label,
                "param_type": p.param_type,
                "required": p.required,
                "default": p.default,
                "placeholder": p.placeholder,
                "hint": p.hint,
                "options": p.options,
            }
            for p in op.params
        ],
        "requires_confirmation": op.operation_type != OperationType.READ,
    }


def get_all_operations_dict() -> list[dict]:
    """Get all operations as serializable dicts."""
    return [operation_to_dict(op) for op in get_all_operations()]


def get_operations_by_category_dict() -> dict[str, list[dict]]:
    """Get operations grouped by category as serializable dicts."""
    by_category = get_operations_by_category()
    return {
        category: [operation_to_dict(op) for op in ops] for category, ops in by_category.items()
    }


def get_available_operations_for_context() -> dict:
    """
    Get available operations considering the current cluster context.

    Returns operations with availability status based on whether
    a cluster is connected.
    """
    cluster_context = get_cluster_context()
    is_connected = cluster_context is not None

    operations = get_all_operations_dict()

    # Mark operations as available/unavailable based on cluster connection
    for op in operations:
        op["available"] = is_connected
        if not is_connected:
            op["unavailable_reason"] = "No Kafka cluster connected"

    return {
        "cluster_connected": is_connected,
        "operations": operations,
        "summary": get_operations_summary(),
    }


def format_operations_for_help() -> str:
    """
    Format operations list for text-based help responses.

    Returns a markdown-formatted string listing all operations.
    """
    by_category = get_operations_by_category()

    lines = ["## Available Kafka Admin Operations\n"]

    for category, ops in by_category.items():
        category_title = category.replace("_", " ").title()
        lines.append(f"### {category_title}\n")

        for op in ops:
            type_badge = ""
            if op.operation_type == OperationType.READ:
                type_badge = "[read]"
            elif op.operation_type == OperationType.WRITE:
                type_badge = "[write]"
            elif op.operation_type == OperationType.DESTRUCTIVE:
                type_badge = "[destructive]"

            lines.append(f"- **{op.name}** {type_badge}")
            lines.append(f"  {op.description}")

            if op.params:
                param_strs = []
                for p in op.params:
                    req = "*" if p.required else ""
                    param_strs.append(f"`{p.name}`{req}")
                lines.append(f"  Parameters: {', '.join(param_strs)}")

            lines.append("")

    lines.append("\n*Required parameters marked with asterisk")

    return "\n".join(lines)


def get_suggested_operations(
    last_operation: str | None = None,
    last_success: bool = True,
    cluster_info: dict | None = None,
) -> list[dict]:
    """
    Get suggested next operations based on context.

    Args:
        last_operation: The ID of the last executed operation
        last_success: Whether the last operation succeeded
        cluster_info: Current cluster metadata

    Returns:
        List of suggested operations with example prompts
    """
    suggestions = []

    # Extract topic and group names from cluster info for substitution
    topics = cluster_info.get("topics", []) if cluster_info else []
    groups = cluster_info.get("consumer_groups", []) if cluster_info else []

    # Get first topic/group for substitution, filtering internal topics
    first_topic = None
    for t in topics:
        if not t.startswith("_"):
            first_topic = t
            break
    if not first_topic and topics:
        first_topic = topics[0]

    first_group = None
    if groups:
        first_group = groups[0].get("group_id") if isinstance(groups[0], dict) else groups[0]

    # After successful operations, suggest related follow-ups
    if last_operation and last_success:
        follow_ups = {
            "create_topic": [
                {"id": "describe_topic", "prompt": "Describe the topic I just created"},
                {"id": "list_topics", "prompt": "Show me all topics now"},
            ],
            "delete_topic": [
                {"id": "list_topics", "prompt": "List remaining topics"},
            ],
            "alter_topic_config": [
                {"id": "describe_topic", "prompt": "Verify the configuration change"},
            ],
            "add_partitions": [
                {"id": "describe_topic", "prompt": "Show the updated partition count"},
            ],
            "list_topics": [
                # Only suggest describe if we have a real topic name
                {
                    "id": "describe_topic",
                    "prompt": f"Describe topic {first_topic}",
                    "requires": "topic",
                },
                {"id": "create_topic", "prompt": "Create a new topic"},
            ],
            "list_consumer_groups": [
                # Only suggest describe if we have a real group
                {
                    "id": "describe_consumer_group",
                    "prompt": f"Describe consumer group {first_group}",
                    "requires": "group",
                },
            ],
            "describe_cluster": [
                {"id": "list_topics", "prompt": "List all topics"},
                {"id": "list_consumer_groups", "prompt": "List consumer groups"},
            ],
            "describe_topic": [
                {"id": "list_topics", "prompt": "List all topics"},
                {
                    "id": "alter_topic_config",
                    "prompt": f"Change retention for {first_topic}",
                    "requires": "topic",
                },
            ],
            "describe_consumer_group": [
                {"id": "list_consumer_groups", "prompt": "List all consumer groups"},
                {
                    "id": "get_consumer_group_offsets",
                    "prompt": f"Get offsets for {first_group}",
                    "requires": "group",
                },
            ],
        }

        if last_operation in follow_ups:
            for follow_up in follow_ups[last_operation]:
                # Skip suggestions that require data we don't have
                requires = follow_up.get("requires")
                if requires == "topic" and not first_topic:
                    continue
                if requires == "group" and not first_group:
                    continue

                op = KAFKA_OPERATIONS.get(follow_up["id"])
                if op:
                    suggestions.append(
                        {
                            "operation_id": follow_up["id"],
                            "operation_name": op.name,
                            "suggested_prompt": follow_up["prompt"],
                            "type": "follow_up",
                        }
                    )

    # If no specific suggestions, provide general ones based on cluster state
    if not suggestions:
        if first_topic:
            suggestions.append(
                {
                    "operation_id": "describe_topic",
                    "operation_name": "Describe Topic",
                    "suggested_prompt": f"Describe topic {first_topic}",
                    "type": "explore",
                }
            )

        if first_group:
            suggestions.append(
                {
                    "operation_id": "describe_consumer_group",
                    "operation_name": "Describe Consumer Group",
                    "suggested_prompt": f"Describe consumer group {first_group}",
                    "type": "explore",
                }
            )

        # Default suggestions
        suggestions.extend(
            [
                {
                    "operation_id": "list_topics",
                    "operation_name": "List Topics",
                    "suggested_prompt": "List all topics in the cluster",
                    "type": "common",
                },
                {
                    "operation_id": "describe_cluster",
                    "operation_name": "Describe Cluster",
                    "suggested_prompt": "Show me cluster status",
                    "type": "common",
                },
            ]
        )

    # Limit to 4 suggestions
    return suggestions[:4]


def get_operation_examples() -> list[dict]:
    """
    Get example prompts for each operation category.

    Returns examples that users can use as templates.
    """
    return [
        {
            "category": "topics",
            "examples": [
                "List all topics",
                "Describe topic orders",
                "Create a topic called events with 6 partitions",
                "Delete topic test-topic",
                "Add 3 more partitions to my-topic",
                "Set retention.ms to 604800000 on topic events",
            ],
        },
        {
            "category": "consumers",
            "examples": [
                "List consumer groups",
                "Describe consumer group my-consumer-group",
                "Show offsets for group my-group",
            ],
        },
        {
            "category": "cluster",
            "examples": [
                "Describe the cluster",
                "Show broker 0 configuration",
            ],
        },
        {
            "category": "security",
            "examples": [
                "List all ACLs",
            ],
        },
    ]

