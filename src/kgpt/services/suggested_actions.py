"""Contextual suggested actions generation based on query and cluster state."""


def generate_suggested_actions(
    message: str,
    cluster_context: dict | None = None,
    admin_result: dict | None = None,
) -> list[dict]:
    """Generate contextual suggested actions based on the query and cluster state."""
    actions = []
    message_lower = message.lower()

    # After admin operation, suggest related follow-ups
    if admin_result:
        operation = admin_result.get("operation", "")
        success = admin_result.get("success", False)

        if success:
            if operation == "delete_topic":
                actions.append(
                    {
                        "id": "list-topics",
                        "label": "List remaining topics",
                        "type": "query",
                        "value": "List all topics in the cluster",
                        "icon": "📋",
                    }
                )
            elif operation == "create_topic":
                topic = admin_result.get("topic", "")
                if topic:
                    actions.append(
                        {
                            "id": "describe-new-topic",
                            "label": f"Describe '{topic}'",
                            "type": "query",
                            "value": f"Describe the configuration of topic {topic}",
                            "icon": "🔍",
                        }
                    )
            elif operation == "alter_topic_config":
                topic = admin_result.get("topic", "")
                if topic:
                    actions.append(
                        {
                            "id": "verify-config",
                            "label": f"Verify '{topic}' config",
                            "type": "query",
                            "value": f"Show the current configuration of topic {topic}",
                            "icon": "✅",
                        }
                    )
        else:
            # On failure, suggest checking cluster status
            actions.append(
                {
                    "id": "check-cluster",
                    "label": "Check cluster status",
                    "type": "query",
                    "value": "Show cluster status and health",
                    "icon": "🔧",
                }
            )

        return actions[:3]

    # Cluster-related suggestions
    if cluster_context:
        topics = cluster_context.get("topics", [])
        consumer_groups = cluster_context.get("consumer_groups", [])

        if "topic" in message_lower and topics:
            # Suggest exploring specific topics
            if len(topics) > 0:
                actions.append(
                    {
                        "id": "describe-topic",
                        "label": f"Describe topic '{topics[0]}'",
                        "type": "query",
                        "value": f"Describe the configuration of topic {topics[0]}",
                        "icon": "📋",
                    }
                )

        # Suggest admin operations for topics
        if "delete" in message_lower or "remove" in message_lower:
            if topics and len(topics) > 0:
                # Find the topic mentioned in the message
                mentioned_topic = next((t for t in topics if t.lower() in message_lower), topics[0])
                actions.append(
                    {
                        "id": "confirm-delete",
                        "label": f"Delete topic '{mentioned_topic}'",
                        "type": "operation",
                        "value": f"Delete the topic {mentioned_topic}",
                        "icon": "🗑️",
                    }
                )

        if "create" in message_lower and "topic" in message_lower:
            actions.append(
                {
                    "id": "create-topic",
                    "label": "Create new topic",
                    "type": "operation",
                    "value": "Create a new topic called my-topic with 3 partitions",
                    "icon": "➕",
                }
            )

        if "consumer" in message_lower or "lag" in message_lower:
            if consumer_groups:
                actions.append(
                    {
                        "id": "check-lag",
                        "label": "Check consumer lag",
                        "type": "query",
                        "value": "Show consumer group lag for all groups",
                        "icon": "⏱️",
                    }
                )

        if "cluster" in message_lower or "status" in message_lower:
            actions.append(
                {
                    "id": "list-topics",
                    "label": "List all topics",
                    "type": "query",
                    "value": "List all topics with their partition counts",
                    "icon": "📋",
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
                "icon": "⚙️",
            }
        )
    if "consumer" in message_lower and "lag" not in message_lower:
        actions.append(
            {
                "id": "consumer-config",
                "label": "Consumer configurations",
                "type": "query",
                "value": "What are the most important consumer configurations?",
                "icon": "⚙️",
            }
        )

    return actions[:3]  # Limit to 3 suggestions
