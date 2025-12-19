"""Help node for responding to 'what can you do' and capability questions."""

from loguru import logger

from kgpt.agents.admin import (
    get_operation_examples,
    get_operations_summary,
    get_suggested_operations,
)
from kgpt.agents.kafka_agent import get_cluster_context
from kgpt.agents.state import AgentState


async def help_node(state: AgentState) -> dict:
    """
    Help node that provides information about available capabilities.

    Returns a structured response with:
    - Overview of what kGPT can do
    - Available operations (dynamically from registry)
    - Example prompts
    - Suggested next actions
    """
    logger.info("Help node providing capabilities overview...")

    # Check cluster connection
    cluster_context = get_cluster_context()
    is_connected = cluster_context is not None

    # Get cluster info if connected
    cluster_info = None
    if cluster_context:
        try:
            cluster_info = cluster_context.get_cluster_metadata()
        except Exception as e:
            logger.warning(f"Failed to get cluster metadata: {e}")

    # Get operations summary
    summary = get_operations_summary()

    # Get examples
    examples = get_operation_examples()

    # Get suggested operations
    suggestions = get_suggested_operations(cluster_info=cluster_info)

    # Build the help response
    help_response = _build_help_response(
        is_connected=is_connected,
        cluster_info=cluster_info,
        summary=summary,
        examples=examples,
        suggestions=suggestions,
    )

    return {
        "help_response": help_response,
        "suggested_prompts": [s["suggested_prompt"] for s in suggestions],
    }


def _build_help_response(
    is_connected: bool,
    cluster_info: dict | None,
    summary: dict,
    examples: list[dict],
    suggestions: list[dict],
) -> dict:
    """Build structured help response for the UI."""

    # Connection status section
    connection_status = {
        "connected": is_connected,
        "message": (
            f"Connected to cluster with {cluster_info.get('broker_count', 0)} broker(s) "
            f"and {cluster_info.get('topic_count', 0)} topic(s)"
            if is_connected and cluster_info
            else "No cluster connected. Connect to a cluster to use admin operations."
        ),
    }

    # Capabilities overview
    capabilities = [
        {
            "title": "Documentation & Knowledge",
            "description": "Ask questions about Kafka concepts, configurations, and best practices",
            "icon": "book",
            "examples": [
                "What is consumer lag?",
                "How do I configure producer retries?",
                "Explain partition rebalancing",
            ],
            "available": True,
        },
        {
            "title": "Cluster Admin Operations",
            "description": f"{summary['total_operations']} operations available for managing your Kafka cluster",
            "icon": "server",
            "examples": [
                "List all topics",
                "Create a topic called events with 6 partitions",
                "Describe consumer group my-group",
            ],
            "available": is_connected,
            "operations_count": {
                "read": summary["read_operations"],
                "write": summary["write_operations"],
                "destructive": summary["destructive_operations"],
            },
        },
        {
            "title": "Real-time Web Search",
            "description": "Search the web for current Kafka articles and updates via Exa",
            "icon": "globe",
            "examples": [
                "What's new in Kafka 4.0?",
                "Latest Kafka security best practices",
            ],
            "available": True,  # Depends on EXA_API_KEY but we show it anyway
        },
    ]

    # Format examples by category
    formatted_examples = []
    for category in examples:
        formatted_examples.append(
            {
                "category": category["category"].replace("_", " ").title(),
                "prompts": category["examples"][:4],  # Limit to 4 per category
            }
        )

    # Suggested actions based on current context
    suggested_actions = []
    for s in suggestions:
        suggested_actions.append(
            {
                "label": s["operation_name"],
                "prompt": s["suggested_prompt"],
                "type": s["type"],
            }
        )

    return {
        "connection": connection_status,
        "capabilities": capabilities,
        "examples_by_category": formatted_examples,
        "suggested_actions": suggested_actions,
        "summary": summary,
    }


def format_help_as_text(help_response: dict) -> str:
    """
    Format the help response as readable text for LLM synthesis.

    Used when the help node feeds into the synthesis node.
    """
    lines = ["# kGPT Capabilities\n"]

    # Connection status
    conn = help_response["connection"]
    if conn["connected"]:
        lines.append(f"**Cluster Status:** {conn['message']}\n")
    else:
        lines.append(
            "**Cluster Status:** Not connected. Connect to a cluster for admin operations.\n"
        )

    # Capabilities
    lines.append("## What I Can Do\n")
    for cap in help_response["capabilities"]:
        available = "Available" if cap["available"] else "Requires cluster connection"
        lines.append(f"### {cap['title']} ({available})")
        lines.append(f"{cap['description']}\n")

        if cap.get("operations_count"):
            counts = cap["operations_count"]
            lines.append(f"- {counts['read']} read-only operations (execute immediately)")
            lines.append(f"- {counts['write']} write operations (require confirmation)")
            lines.append(
                f"- {counts['destructive']} destructive operations (require explicit confirmation)\n"
            )

        lines.append("**Examples:**")
        for ex in cap["examples"]:
            lines.append(f'- "{ex}"')
        lines.append("")

    # Suggested next steps
    if help_response["suggested_actions"]:
        lines.append("## Suggested Next Steps\n")
        for action in help_response["suggested_actions"]:
            lines.append(f'- {action["label"]}: "{action["prompt"]}"')

    return "\n".join(lines)

