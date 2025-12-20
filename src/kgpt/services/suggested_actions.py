"""Contextual suggested actions generation based on query and cluster state."""

# from kgpt.agents.admin import get_suggested_operations


def get_suggested_operations(
    last_operation: str, last_success: bool, cluster_info: dict | None = None
) -> list[dict]:
    """
    Generate suggested follow-up operations based on the last operation.
    Simplified local implementation since admin module is removed.
    """
    suggestions = []

    if not last_success:
        return []

    op_lower = last_operation.lower()

    if "create" in op_lower and "topic" in op_lower:
        suggestions.append(
            {
                "operation_id": "describe-created-topic",
                "operation_name": "Describe new topic",
                "suggested_prompt": "Describe topic [topic_name]",
            }
        )
        suggestions.append(
            {
                "operation_id": "list-topics",
                "operation_name": "List topics",
                "suggested_prompt": "List all topics",
            }
        )

    elif "delete" in op_lower and "topic" in op_lower:
        suggestions.append(
            {
                "operation_id": "list-topics",
                "operation_name": "Verify deletion",
                "suggested_prompt": "List all topics to verify deletion",
            }
        )

    elif "group" in op_lower:
        suggestions.append(
            {
                "operation_id": "list-groups",
                "operation_name": "List consumer groups",
                "suggested_prompt": "List all consumer groups",
            }
        )

    return suggestions


def generate_suggested_actions(
    message: str,
    cluster_context: dict | None = None,
    admin_result: dict | None = None,
) -> list[dict]:
    """
    Generate contextual suggested actions based on the query and cluster state.

    Uses the operations discovery module for dynamic operation suggestions,
    combined with documentation-related suggestions based on the message content.
    """
    actions = []
    message_lower = message.lower()

    # After admin operation, use the discovery module for follow-up suggestions
    if admin_result:
        operation = admin_result.get("operation", "")
        success = admin_result.get("success", False)

        # Get dynamic suggestions based on the operation
        suggestions = get_suggested_operations(
            last_operation=operation,
            last_success=success,
            cluster_info=cluster_context,
        )

        for s in suggestions:
            # Customize the prompt if we have specific data from the result
            prompt = s["suggested_prompt"]

            # Replace placeholders with actual values from the result
            if "[topic_name]" in prompt and admin_result.get("topic"):
                prompt = prompt.replace("[topic_name]", admin_result["topic"])
            if "[group_id]" in prompt and admin_result.get("group_id"):
                prompt = prompt.replace("[group_id]", admin_result["group_id"])

            actions.append(
                {
                    "id": s["operation_id"],
                    "label": s["operation_name"],
                    "type": "query",
                    "value": prompt,
                }
            )

        # Add failure recovery suggestion
        if not success:
            actions.append(
                {
                    "id": "check-cluster",
                    "label": "Check cluster status",
                    "type": "query",
                    "value": "Describe the cluster",
                }
            )

        return actions[:3]

    # For non-admin responses, combine topic-aware and documentation suggestions

    # Cluster-related suggestions
    if cluster_context:
        topics = cluster_context.get("topics", [])
        consumer_groups = cluster_context.get("consumer_groups", [])

        # Topic-specific suggestions
        if "topic" in message_lower and topics:
            if len(topics) > 0:
                actions.append(
                    {
                        "id": "describe-topic",
                        "label": f"Describe topic '{topics[0]}'",
                        "type": "query",
                        "value": f"Describe topic {topics[0]}",
                    }
                )

        # Admin operation suggestions based on intent
        if "delete" in message_lower or "remove" in message_lower:
            if topics and len(topics) > 0:
                mentioned_topic = next((t for t in topics if t.lower() in message_lower), topics[0])
                actions.append(
                    {
                        "id": "confirm-delete",
                        "label": f"Delete topic '{mentioned_topic}'",
                        "type": "operation",
                        "value": f"Delete topic {mentioned_topic}",
                    }
                )

        if "create" in message_lower and "topic" in message_lower:
            actions.append(
                {
                    "id": "create-topic",
                    "label": "Create new topic",
                    "type": "operation",
                    "value": "Create a topic called my-topic with 3 partitions",
                }
            )

        if "consumer" in message_lower or "lag" in message_lower:
            if consumer_groups:
                group_id = (
                    consumer_groups[0].get("group_id")
                    if isinstance(consumer_groups[0], dict)
                    else consumer_groups[0]
                )
                actions.append(
                    {
                        "id": "describe-group",
                        "label": "Describe consumer group",
                        "type": "query",
                        "value": f"Describe consumer group {group_id}",
                    }
                )

        if "cluster" in message_lower or "status" in message_lower:
            actions.append(
                {
                    "id": "list-topics",
                    "label": "List all topics",
                    "type": "query",
                    "value": "List all topics",
                }
            )

    # Documentation-related suggestions
    if "producer" in message_lower:
        actions.append(
            {
                "id": "producer-config",
                "label": "Producer configurations",
                "type": "query",
                "value": "What are the most important producer configurations?",
            }
        )

    if "consumer" in message_lower and "lag" not in message_lower:
        actions.append(
            {
                "id": "consumer-config",
                "label": "Consumer configurations",
                "type": "query",
                "value": "What are the most important consumer configurations?",
            }
        )

    if "partition" in message_lower:
        actions.append(
            {
                "id": "partition-info",
                "label": "Partition best practices",
                "type": "query",
                "value": "How do I choose the right number of partitions?",
            }
        )

    if "replication" in message_lower or "replica" in message_lower:
        actions.append(
            {
                "id": "replication-info",
                "label": "Replication explained",
                "type": "query",
                "value": "How does Kafka replication work?",
            }
        )

    # If no suggestions yet, provide helpful defaults
    if not actions:
        actions.extend(
            [
                {
                    "id": "help",
                    "label": "What can you do?",
                    "type": "query",
                    "value": "What operations are available?",
                },
                {
                    "id": "list-topics",
                    "label": "List topics",
                    "type": "query",
                    "value": "List all topics",
                },
            ]
        )

    return actions[:3]  # Limit to 3 suggestions
