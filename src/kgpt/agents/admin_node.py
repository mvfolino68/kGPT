"""Admin agent for executing Kafka cluster operations.

This module provides intelligent routing of admin commands:
- Read operations execute immediately and show results
- Write/destructive operations show confirmation UI
- LLM intelligently maps natural language to operations
"""

from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field

from kgpt.agents.admin import (
    OperationType,
    get_all_operations,
    get_executor,
    get_operation,
)
from kgpt.agents.kafka_agent import get_cluster_context
from kgpt.agents.state import AgentState
from kgpt.llm import get_structured_llm

# ============================================================================
# LLM Structured Output Models
# ============================================================================


class ExtractedParams(BaseModel):
    """Parameters extracted from user's request."""

    model_config = ConfigDict(extra="forbid")

    topic_name: str | None = Field(default=None, description="Topic name if mentioned")
    group_id: str | None = Field(default=None, description="Consumer group ID if mentioned")
    num_partitions: int | None = Field(default=None, description="Number of partitions")
    replication_factor: int | None = Field(default=None, description="Replication factor")
    new_total_partitions: int | None = Field(
        default=None, description="New total partitions for add_partitions"
    )
    config_key: str | None = Field(default=None, description="Config key for alter_topic_config")
    config_value: str | None = Field(
        default=None, description="Config value for alter_topic_config"
    )
    broker_id: int | None = Field(default=None, description="Broker ID for broker operations")


class OperationMapping(BaseModel):
    """Maps user intent to a specific operation."""

    model_config = ConfigDict(extra="forbid")

    operation_id: str | None = Field(
        default=None,
        description="The operation ID to execute (e.g., 'list_topics', 'describe_topic')",
    )
    confidence: Literal["high", "medium", "low"] = Field(
        default="medium",
        description="How confident are we in this mapping",
    )
    params: ExtractedParams = Field(
        default_factory=ExtractedParams,
        description="Extracted parameters from the user's request",
    )
    missing_params: list[str] = Field(
        default_factory=list,
        description="Required parameters that are missing",
    )
    reasoning: str = Field(
        default="",
        description="Brief explanation of the mapping decision",
    )


# ============================================================================
# Prompt for Operation Mapping
# ============================================================================


def build_operation_list() -> str:
    """Build a formatted list of available operations for the prompt."""
    operations = get_all_operations()
    lines = []
    for op in operations:
        param_names = [p.name for p in op.params]
        param_str = f"(params: {', '.join(param_names)})" if param_names else "(no params)"
        op_type = "READ" if op.operation_type == OperationType.READ else "WRITE"
        lines.append(f"- {op.id}: {op.description} [{op_type}] {param_str}")
    return "\n".join(lines)


OPERATION_MAPPER_SYSTEM_PROMPT = """You are a Kafka admin assistant that maps user requests to specific operations.

### Available Operations:
{operations}

### Instructions:
1. Analyze the user's request and determine which operation they want
2. Extract any parameters mentioned in the request
3. If parameters are missing but required, list them in missing_params
4. Set confidence based on how clear the user's intent is

### Parameter Extraction:
- Topic names: Look for topic names in quotes or after keywords like "topic", "for"
- Group IDs: Look for consumer group names/IDs
- Numbers: Extract partition counts, replication factors, broker IDs
- Config values: Look for key=value patterns or "set X to Y" phrases

### Examples:
- "list all topics" -> operation_id="list_topics", params={{}}
- "describe topic orders" -> operation_id="describe_topic", params={{"topic_name": "orders"}}
- "what are the partitions for users topic" -> operation_id="describe_topic", params={{"topic_name": "users"}}
- "show me consumer groups" -> operation_id="list_consumer_groups", params={{}}
- "delete topic test-topic" -> operation_id="delete_topic", params={{"topic_name": "test-topic"}}
- "create a topic called events with 5 partitions" -> operation_id="create_topic", params={{"topic_name": "events", "num_partitions": 5}}
- "describe the cluster" -> operation_id="describe_cluster", params={{}}
- "what topics exist" -> operation_id="list_topics", params={{}}"""


OPERATION_MAPPER_USER_PROMPT = """Map this request to a Kafka operation:

User request: {question}

Current cluster context:
- Topics: {topics}
- Consumer groups: {groups}
- Broker count: {broker_count}

Respond with the operation mapping:"""


async def map_request_to_operation(question: str, cluster_info: dict | None) -> OperationMapping:
    """Use LLM to map user request to a specific operation."""
    llm = get_structured_llm(temperature=0)
    structured_llm = llm.with_structured_output(OperationMapping)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", OPERATION_MAPPER_SYSTEM_PROMPT),
            ("human", OPERATION_MAPPER_USER_PROMPT),
        ]
    )

    topics = cluster_info.get("topics", []) if cluster_info else []
    groups = cluster_info.get("consumer_groups", []) if cluster_info else []
    broker_count = cluster_info.get("broker_count", 1) if cluster_info else 1

    group_ids = [g.get("group_id", str(g)) if isinstance(g, dict) else str(g) for g in groups]

    chain = prompt | structured_llm

    try:
        result = await chain.ainvoke(
            {
                "operations": build_operation_list(),
                "question": question,
                "topics": ", ".join(topics[:20]) if topics else "none",
                "groups": ", ".join(group_ids[:20]) if group_ids else "none",
                "broker_count": broker_count,
            }
        )
        return result
    except Exception as e:
        logger.error(f"Failed to map operation: {e}")
        return OperationMapping(
            operation_id=None,
            confidence="low",
            reasoning=f"Failed to parse request: {str(e)}",
        )


# ============================================================================
# Admin Node
# ============================================================================


async def admin_node(state: AgentState) -> dict:
    """
    Admin agent node that handles Kafka admin operations.

    Key behaviors:
    - READ operations execute immediately and return results
    - WRITE/DESTRUCTIVE operations return confirmation UI
    - Always provides a response (never leaves user hanging)
    """
    logger.info("Admin agent processing request...")

    context = get_cluster_context()
    if context is None:
        logger.warning("No Kafka cluster configured for admin operation")
        return {
            "admin_result": {
                "success": False,
                "error": "No Kafka cluster connected. Please connect to a cluster first.",
                "needs_response": True,
            },
            "error": "No Kafka cluster connected.",
        }

    try:
        # Get cluster info for context
        cluster_info = context.get_cluster_metadata()

        # Map the user's request to an operation
        mapping = await map_request_to_operation(state["question"], cluster_info)

        # Convert params to dict, excluding None values
        params_dict = mapping.params.model_dump(exclude_none=True)

        logger.info(
            f"Operation mapping: {mapping.operation_id} "
            f"(confidence={mapping.confidence}, params={params_dict})"
        )

        # If we couldn't determine the operation
        if not mapping.operation_id:
            return {
                "admin_result": {
                    "success": False,
                    "unclear": True,
                    "guidance_message": mapping.reasoning
                    or "I couldn't understand what operation you want. Try asking to list topics, describe a topic, or manage consumer groups.",
                    "available_operations": _get_operation_suggestions(),
                    "needs_response": True,
                },
                "cluster_context": cluster_info,
            }

        # Get the operation definition
        operation = get_operation(mapping.operation_id)
        if not operation:
            return {
                "admin_result": {
                    "success": False,
                    "error": f"Unknown operation: {mapping.operation_id}",
                    "needs_response": True,
                },
                "cluster_context": cluster_info,
            }

        # Apply smart defaults based on cluster state
        params_dict = _apply_smart_defaults(params_dict, mapping.operation_id, cluster_info)

        # Check for missing required parameters
        # Filter out optional params - only flag as needs_info if required params are missing
        required_param_names = {p.name for p in operation.params if p.required}
        actually_missing = [p for p in mapping.missing_params if p in required_param_names]

        if actually_missing:
            return {
                "admin_result": {
                    "success": True,
                    "needs_info": True,
                    "operation": mapping.operation_id,
                    "operation_title": operation.name,
                    "params": params_dict,
                    "input_fields": _build_input_fields(operation, actually_missing),
                    "guidance_message": f"Please provide: {', '.join(actually_missing)}",
                    "needs_response": True,
                },
                "cluster_context": cluster_info,
            }

        # Get executor
        executor = get_executor()
        if not executor:
            return {
                "admin_result": {
                    "success": False,
                    "error": "Could not create executor - cluster not connected",
                    "needs_response": True,
                },
            }

        # Check if this is a read operation (execute immediately)
        if operation.operation_type == OperationType.READ:
            logger.info(f"Executing read operation: {mapping.operation_id}")
            result = executor.execute(mapping.operation_id, params_dict)

            return {
                "admin_result": {
                    "success": result.success,
                    "executed": True,
                    "operation": result.operation_id,
                    "operation_name": result.operation_name,
                    "data": result.data,
                    "message": result.message,
                    "error": result.error,
                    "code_executed": result.code_executed,
                    "needs_response": True,
                },
                "cluster_context": cluster_info,
            }

        # Write/destructive operation - needs confirmation
        warning_level = (
            "high" if operation.operation_type == OperationType.DESTRUCTIVE else "medium"
        )
        confirmation_message = _build_confirmation_message(operation, params_dict)
        warning_message = (
            _build_warning_message(operation, params_dict)
            if operation.operation_type == OperationType.DESTRUCTIVE
            else ""
        )

        return {
            "admin_result": {
                "success": True,
                "pending": True,
                "operation": mapping.operation_id,
                "operation_title": operation.name,
                "params": params_dict,
                "confirmation_message": confirmation_message,
                "warning_level": warning_level,
                "warning_message": warning_message,
                "code_preview": operation.get_code_preview(params_dict),
                "needs_response": True,
            },
            "cluster_context": cluster_info,
            "admin_operation": {"type": mapping.operation_id, "params": params_dict},
        }

    except Exception as e:
        logger.error(f"Admin agent error: {e}", exc_info=True)
        return {
            "admin_result": {
                "success": False,
                "error": f"Failed to process admin request: {str(e)}",
                "needs_response": True,
            },
            "error": str(e),
        }


def _apply_smart_defaults(params: dict, operation_id: str, cluster_info: dict | None) -> dict:
    """
    Apply intelligent defaults based on cluster state.

    For example, set replication_factor to min(3, broker_count) for create_topic.
    """
    if operation_id != "create_topic":
        return params

    # If replication_factor is already specified, don't override
    if params.get("replication_factor") is not None:
        return params

    # Get broker count from cluster info
    broker_count = 1
    if cluster_info:
        broker_count = cluster_info.get("broker_count", 1)

    # Smart default: min(3, broker_count) for fault tolerance
    # 3 is the production best practice, but can't exceed broker count
    smart_rf = min(3, broker_count)

    logger.debug(f"Smart default: replication_factor={smart_rf} (broker_count={broker_count})")

    return {**params, "replication_factor": smart_rf}


def _get_operation_suggestions() -> list[dict]:
    """Get suggestions for available operations."""
    return [
        {"id": "list_topics", "label": "List all topics", "icon": "list"},
        {"id": "describe_topic", "label": "Describe a topic", "icon": "info"},
        {"id": "create_topic", "label": "Create a new topic", "icon": "plus"},
        {"id": "list_consumer_groups", "label": "List consumer groups", "icon": "users"},
        {"id": "describe_cluster", "label": "Describe the cluster", "icon": "server"},
    ]


def _build_input_fields(operation, missing_params: list[str]) -> list[dict]:
    """Build input field definitions for missing parameters."""
    fields = []
    for param in operation.params:
        if param.name in missing_params:
            fields.append(
                {
                    "name": param.name,
                    "label": param.label,
                    "field_type": param.param_type,
                    "required": param.required,
                    "default": param.default,
                    "placeholder": param.placeholder,
                    "hint": param.hint,
                    "options": param.options,
                }
            )
    return fields


def _build_confirmation_message(operation, params: dict) -> str:
    """Build a human-readable confirmation message."""
    messages = {
        "create_topic": lambda p: f"Create topic '{p.get('topic_name')}' with {p.get('num_partitions', 3)} partition(s) and replication factor {p.get('replication_factor', 1)}",
        "delete_topic": lambda p: f"Delete topic '{p.get('topic_name')}' and all its data",
        "add_partitions": lambda p: f"Increase partitions for '{p.get('topic_name')}' to {p.get('new_total_partitions')}",
        "alter_topic_config": lambda p: f"Set {p.get('config_key')}={p.get('config_value')} on topic '{p.get('topic_name')}'",
        "delete_consumer_group": lambda p: f"Delete consumer group '{p.get('group_id')}'",
    }

    builder = messages.get(operation.id)
    if builder:
        return builder(params)
    return f"Execute {operation.name}"


def _build_warning_message(operation, params: dict) -> str:
    """Build a warning message for destructive operations."""
    if operation.id == "delete_topic":
        return f"This will permanently delete topic '{params.get('topic_name')}' and all its messages. This cannot be undone!"
    if operation.id == "delete_consumer_group":
        return f"This will delete consumer group '{params.get('group_id')}'. Make sure no consumers are active."
    return "This operation may have significant impact. Please review carefully."


# ============================================================================
# Execute Confirmed Operation
# ============================================================================


async def execute_confirmed_operation(operation: str, params: dict) -> dict:
    """
    Execute a confirmed admin operation.

    This should only be called after the user has explicitly confirmed the operation.
    """
    logger.info(f"Executing confirmed operation: {operation} with params: {params}")

    executor = get_executor()
    if executor is None:
        return {
            "success": False,
            "error": "No Kafka cluster connected.",
        }

    try:
        result = executor.execute(operation, params)
        return result.to_dict()
    except Exception as e:
        logger.error(f"Operation execution error: {e}")
        return {
            "success": False,
            "operation": operation,
            "error": f"Failed to execute operation: {str(e)}",
        }
