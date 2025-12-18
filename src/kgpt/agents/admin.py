"""Admin agent for executing Kafka cluster operations."""

import json
import re
from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field

from kgpt.agents.kafka_agent import get_cluster_context
from kgpt.agents.state import AgentState
from kgpt.llm import get_structured_llm

# ============================================================================
# Structured Output Models for Admin Operations
# ============================================================================


class InputField(BaseModel):
    """A single input field the user needs to provide."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="Parameter name (e.g., 'topic_name')")
    label: str = Field(description="Human-readable label (e.g., 'Topic Name')")
    field_type: Literal["text", "number", "select"] = Field(
        default="text", description="Type of input field"
    )
    required: bool = Field(default=True, description="Whether this field is required")
    default: str | int | None = Field(default=None, description="Default value if any")
    placeholder: str = Field(default="", description="Placeholder text for the input")
    hint: str = Field(default="", description="Help text explaining this field")
    options: list[str] = Field(default_factory=list, description="Options for select fields")


class OperationParams(BaseModel):
    """Parameters for a Kafka admin operation."""

    model_config = ConfigDict(extra="forbid")

    # Topic parameters
    topic_name: str | None = Field(default=None, description="Name of the topic")
    num_partitions: int | None = Field(default=None, description="Number of partitions")
    replication_factor: int | None = Field(default=None, description="Replication factor")
    new_total_partitions: int | None = Field(
        default=None, description="New total number of partitions for add_partitions"
    )
    config_key: str | None = Field(default=None, description="Configuration key to modify")
    config_value: str | None = Field(default=None, description="Configuration value to set")

    # Consumer group parameters
    group_id: str | None = Field(default=None, description="Consumer group ID")


class AdminAnalysisResult(BaseModel):
    """Structured result from analyzing an admin operation request."""

    model_config = ConfigDict(extra="forbid")

    operation: str | None = Field(
        default=None,
        description="Operation type: create_topic, delete_topic, describe_topic, alter_topic_config, delete_consumer_group, add_partitions, describe_consumer_group, or null if unclear",
    )
    operation_title: str = Field(
        description="Human-readable title for the operation (e.g., 'Create New Topic')"
    )
    status: Literal["ready", "needs_info", "unclear"] = Field(
        description="Whether we have all info needed"
    )
    params: OperationParams = Field(
        default_factory=OperationParams, description="Parameters provided so far"
    )
    input_fields: list[InputField] = Field(
        default_factory=list,
        description="Input fields to show the user (for needs_info status)",
    )
    confirmation_message: str = Field(
        default="", description="What will happen if confirmed (for ready status)"
    )
    warning_level: Literal["low", "medium", "high"] = Field(
        default="medium", description="Risk level of the operation"
    )
    warning_message: str = Field(
        default="", description="Warning to show user (for high-risk operations)"
    )
    guidance_message: str = Field(
        default="", description="Helpful message guiding the user on next steps"
    )


# ============================================================================
# Prompts
# ============================================================================

ADMIN_ANALYZER_SYSTEM_PROMPT = """You are a Kafka admin assistant. Analyze the user's request and determine what they want to do.

### Supported Operations:
1. **create_topic**: Create a new topic
   - Required: topic_name
   - Optional: num_partitions (default 1), replication_factor (default 1)

2. **delete_topic**: Delete a topic
   - Required: topic_name

3. **describe_topic**: Get detailed information about a topic (partitions, replicas, configuration)
   - Required: topic_name

4. **alter_topic_config**: Modify topic configuration
   - Required: topic_name, config_key, config_value

5. **delete_consumer_group**: Delete a consumer group
   - Required: group_id

6. **add_partitions**: Add partitions to a topic
   - Required: topic_name, new_total_partitions

7. **describe_consumer_group**: Get details about a consumer group
   - Required: group_id

### Response Guidelines:
- If the user's intent is clear but missing required info, set status="needs_info" and provide input_fields
- If all required info is provided, set status="ready" with confirmation details
- If intent is unclear, set status="unclear" and ask a clarifying question in guidance_message
- For delete operations, always set warning_level="high" and include a warning_message
- Make input field labels and hints user-friendly and helpful
- Provide sensible defaults where applicable (e.g., partitions=3, replication_factor=1)

### Required Response Format:
- operation_title: Human-readable title (REQUIRED field)
- input_fields: Array of objects with fields: name, label, field_type ("text", "number", or "select"), required, default, placeholder, hint, options
- field_type must be exactly "text", "number", or "select" (not "string", "integer", etc.)
- Use "name" (not "field_name") for input field parameter names"""

ADMIN_ANALYZER_USER_PROMPT = """Analyze this admin operation request:

User request: {question}

Cluster context:
- Available topics: {topics}
- Consumer groups: {groups}
- Number of brokers: {broker_count}

Provide your structured analysis:"""


def extract_json(text: str) -> dict:
    """Extract JSON from text that may contain additional content or markdown code blocks."""
    # First, try to parse as-is
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Try to extract JSON from markdown code blocks (```json ... ```)
    markdown_json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if markdown_json_match:
        try:
            return json.loads(markdown_json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find JSON with nested objects (greedy match)
    json_match = re.search(r"\{.*\}", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    # Try simpler match
    json_match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not extract valid JSON from: {text[:200]}")


def normalize_admin_analysis_result(data: dict) -> dict:
    """
    Normalize LLM response to match AdminAnalysisResult schema.

    Handles common variations in field names and types that LLMs might use.
    """
    normalized = {}

    # Map top-level fields
    field_mappings = {
        "operation": "operation",
        "operation_title": "operation_title",
        "title": "operation_title",  # Alternative name
        "status": "status",
        "params": "params",
        "parameters": "params",  # Alternative name
        "input_fields": "input_fields",
        "fields": "input_fields",  # Alternative name
        "confirmation_message": "confirmation_message",
        "confirmation": "confirmation_message",  # Alternative name
        "warning_level": "warning_level",
        "warning_message": "warning_message",
        "warning": "warning_message",  # Alternative name
        "guidance_message": "guidance_message",
        "guidance": "guidance_message",  # Alternative name
        "message": "guidance_message",  # Alternative name
    }

    for key, value in data.items():
        normalized_key = field_mappings.get(key, key)
        normalized[normalized_key] = value

    # Ensure operation is set if we can infer it from input_fields
    if not normalized.get("operation") and normalized.get("input_fields"):
        # Try to infer operation from required fields
        input_field_names = [
            f.get("name") or f.get("field_name")
            for f in normalized["input_fields"]
            if isinstance(f, dict)
        ]
        if "topic_name" in input_field_names and "num_partitions" in input_field_names:
            normalized["operation"] = "create_topic"
        elif "topic_name" in input_field_names and "new_total_partitions" in input_field_names:
            normalized["operation"] = "add_partitions"
        elif "topic_name" in input_field_names and "config_key" in input_field_names:
            normalized["operation"] = "alter_topic_config"
        elif "topic_name" in input_field_names and len(input_field_names) == 1:
            # Only topic_name - could be describe_topic or delete_topic
            # Default to describe_topic as it's safer (read-only)
            normalized["operation"] = "describe_topic"
        elif "topic_name" in input_field_names:
            # Could be delete_topic or describe_topic, but we can't be sure without more context
            pass
        elif "group_id" in input_field_names:
            # Could be delete_consumer_group or describe_consumer_group
            pass

    # Ensure operation_title exists (required field)
    if "operation_title" not in normalized:
        operation = normalized.get("operation", "")
        if operation:
            # Generate a title from operation
            title_map = {
                "create_topic": "Create New Topic",
                "delete_topic": "Delete Topic",
                "describe_topic": "Describe Topic",
                "alter_topic_config": "Modify Topic Configuration",
                "add_partitions": "Add Partitions",
                "delete_consumer_group": "Delete Consumer Group",
                "describe_consumer_group": "Describe Consumer Group",
            }
            normalized["operation_title"] = title_map.get(operation, "Kafka Admin Operation")
        else:
            normalized["operation_title"] = "Kafka Admin Operation"

    # Normalize input_fields
    if "input_fields" in normalized and isinstance(normalized["input_fields"], list):
        normalized_fields = []
        for field in normalized["input_fields"]:
            if not isinstance(field, dict):
                continue

            normalized_field = {}

            # Map field name (field_name -> name) - skip if no name found
            field_name = field.get("name") or field.get("field_name")
            if not field_name:
                continue  # Skip fields without a name

            normalized_field["name"] = field_name

            # Map label (use name if label not provided)
            normalized_field["label"] = field.get("label") or field_name

            # Map field_type (string -> text, integer -> number)
            field_type = field.get("field_type") or field.get("type") or "text"
            type_mapping = {
                "string": "text",
                "str": "text",
                "text": "text",
                "integer": "number",
                "int": "number",
                "number": "number",
                "numeric": "number",
                "select": "select",
                "dropdown": "select",
            }
            normalized_field["field_type"] = type_mapping.get(field_type.lower(), "text")

            # Map other fields
            normalized_field["required"] = field.get("required", True)
            normalized_field["default"] = field.get("default") or field.get("suggested_value")
            normalized_field["placeholder"] = field.get("placeholder") or field.get("hint") or ""

            # Combine hint/validation/note into hint
            hint_parts = []
            if field.get("hint"):
                hint_parts.append(field["hint"])
            if field.get("validation"):
                hint_parts.append(field["validation"])
            if field.get("note"):
                hint_parts.append(field["note"])
            normalized_field["hint"] = " ".join(hint_parts)

            # Options for select fields - normalize to list of strings
            options_raw = field.get("options") or field.get("choices") or []
            normalized_options = []
            for opt in options_raw:
                if isinstance(opt, str):
                    normalized_options.append(opt)
                elif isinstance(opt, dict):
                    # Extract value from object format {value: 'x', label: 'y'}
                    normalized_options.append(opt.get("value") or opt.get("label") or str(opt))
                else:
                    normalized_options.append(str(opt))
            normalized_field["options"] = normalized_options

            # Add the normalized field
            normalized_fields.append(normalized_field)

        normalized["input_fields"] = normalized_fields

    # Normalize params - ensure it's always a dict
    if "params" not in normalized or not isinstance(normalized.get("params"), dict):
        normalized["params"] = {}
    else:
        # Remove any extra fields from params
        allowed_params = {
            "topic_name",
            "num_partitions",
            "replication_factor",
            "new_total_partitions",
            "config_key",
            "config_value",
            "group_id",
        }
        normalized["params"] = {
            k: v for k, v in normalized["params"].items() if k in allowed_params
        }

    # Ensure status has a default value
    if "status" not in normalized:
        normalized["status"] = "unclear"

    # Ensure input_fields is always a list
    if "input_fields" not in normalized:
        normalized["input_fields"] = []

    # Ensure other optional fields have defaults
    if "confirmation_message" not in normalized:
        normalized["confirmation_message"] = ""
    if "warning_level" not in normalized:
        normalized["warning_level"] = "medium"
    if "warning_message" not in normalized:
        normalized["warning_message"] = ""
    if "guidance_message" not in normalized:
        normalized["guidance_message"] = ""

    # Remove extra fields not in schema
    allowed_fields = {
        "operation",
        "operation_title",
        "status",
        "params",
        "input_fields",
        "confirmation_message",
        "warning_level",
        "warning_message",
        "guidance_message",
    }
    normalized = {k: v for k, v in normalized.items() if k in allowed_fields}

    return normalized


async def analyze_admin_request(question: str, cluster_context: dict | None) -> AdminAnalysisResult:
    """
    Analyze the user's request using structured output.

    Uses native LangChain models (ChatOpenAI/ChatAnthropic) that support
    the with_structured_output() method for reliable Pydantic model responses.

    Falls back to JSON extraction if the model returns a string wrapped in markdown.
    """
    # Get a native LangChain model that supports structured output
    llm = get_structured_llm(temperature=0)

    # Bind the Pydantic model for structured output
    structured_llm = llm.with_structured_output(AdminAnalysisResult)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", ADMIN_ANALYZER_SYSTEM_PROMPT),
            ("human", ADMIN_ANALYZER_USER_PROMPT),
        ]
    )

    topics = cluster_context.get("topics", []) if cluster_context else []
    groups = cluster_context.get("consumer_groups", []) if cluster_context else []
    broker_count = cluster_context.get("broker_count", 1) if cluster_context else 1

    # Format groups for display
    group_ids = [g.get("group_id", str(g)) if isinstance(g, dict) else str(g) for g in groups]

    input_vars = {
        "question": question,
        "topics": ", ".join(topics[:20]) if topics else "none",
        "groups": ", ".join(group_ids[:20]) if group_ids else "none",
        "broker_count": broker_count,
    }

    chain = prompt | structured_llm

    try:
        result = await chain.ainvoke(input_vars)
    except Exception as e:
        # If structured output fails (e.g., JSON wrapped in markdown), try fallback
        error_str = str(e)
        logger.warning(f"Structured output failed, attempting fallback: {error_str[:200]}")

        # Try to extract JSON from error message if it contains the response
        # Pydantic validation errors often include input_value in the error message
        if "```json" in error_str or "```" in error_str or "input_value" in error_str:
            try:
                # Try to extract JSON from the error string
                json_data = extract_json(error_str)
                normalized_data = normalize_admin_analysis_result(json_data)
                return AdminAnalysisResult(**normalized_data)
            except Exception as parse_error:
                logger.debug(f"Could not extract JSON from error message: {parse_error}")

        # Also try to get input_value from Pydantic ValidationError if available
        if hasattr(e, "errors") and isinstance(e.errors, list):
            for error_detail in e.errors:
                if "input_value" in error_detail:
                    try:
                        input_val = error_detail["input_value"]
                        if isinstance(input_val, str):
                            json_data = extract_json(input_val)
                        elif isinstance(input_val, dict):
                            json_data = input_val
                        else:
                            continue
                        normalized_data = normalize_admin_analysis_result(json_data)
                        return AdminAnalysisResult(**normalized_data)
                    except Exception as parse_err:
                        logger.debug(f"Could not normalize from error detail: {parse_err}")
                        pass

        # Fallback: call LLM without structured output and parse manually
        logger.info("Falling back to manual JSON extraction...")
        regular_llm = get_structured_llm(temperature=0)
        regular_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    ADMIN_ANALYZER_SYSTEM_PROMPT
                    + "\n\nIMPORTANT: Respond with ONLY valid JSON, no markdown code blocks, no explanations.",
                ),
                ("human", ADMIN_ANALYZER_USER_PROMPT),
            ]
        )
        regular_chain = regular_prompt | regular_llm
        raw_response = await regular_chain.ainvoke(input_vars)

        # Extract JSON from response (handle both AIMessage objects and strings)
        response_text = (
            raw_response.content if hasattr(raw_response, "content") else str(raw_response)
        )
        json_data = extract_json(response_text)
        normalized_data = normalize_admin_analysis_result(json_data)
        return AdminAnalysisResult(**normalized_data)

    # Handle case where structured output returns a string (e.g., JSON wrapped in markdown)
    if isinstance(result, str):
        logger.warning("Structured output returned a string, extracting JSON...")
        try:
            json_data = extract_json(result)
            normalized_data = normalize_admin_analysis_result(json_data)
            return AdminAnalysisResult(**normalized_data)
        except Exception as e:
            logger.error(f"Failed to parse structured output: {e}")
            raise ValueError(f"Failed to parse admin analysis result: {e}") from e

    # If it's already a Pydantic model, return it directly
    if isinstance(result, AdminAnalysisResult):
        return result

    # If it's a dict, normalize and convert to Pydantic model
    if isinstance(result, dict):
        normalized_data = normalize_admin_analysis_result(result)
        return AdminAnalysisResult(**normalized_data)

    # Unexpected type
    raise ValueError(f"Unexpected result type from structured output: {type(result)}")


async def admin_node(state: AgentState) -> dict:
    """
    Admin agent node that analyzes admin operation requests.

    Uses structured output to determine:
    - What operation the user wants
    - What input fields to show
    - What information is still needed

    Returns structured data for the frontend to render beautiful UI cards.
    """
    logger.info("Admin agent analyzing operation request...")

    context = get_cluster_context()

    if context is None:
        logger.warning("No Kafka cluster configured for admin operation")
        return {
            "admin_result": {
                "success": False,
                "error": "No Kafka cluster connected. Please connect to a cluster first.",
            },
            "error": "No Kafka cluster connected.",
        }

    try:
        # First, get cluster info for context
        cluster_info = context.get_cluster_metadata()

        # Analyze the request using structured output
        analysis = await analyze_admin_request(state["question"], cluster_info)

        logger.info(f"Admin analysis: status={analysis.status}, operation={analysis.operation}")

        # Convert params to dict, excluding None values for cleaner output
        params_dict = analysis.params.model_dump(exclude_none=True)

        if analysis.status == "ready":
            # All information gathered - return for confirmation
            return {
                "admin_result": {
                    "success": True,
                    "pending": True,  # Awaiting user confirmation
                    "operation": analysis.operation,
                    "operation_title": analysis.operation_title,
                    "params": params_dict,
                    "confirmation_message": analysis.confirmation_message,
                    "warning_level": analysis.warning_level,
                    "warning_message": analysis.warning_message,
                },
                "cluster_context": cluster_info,
                "admin_operation": {"type": analysis.operation, "params": params_dict},
            }

        elif analysis.status == "needs_info":
            # Need more information - return input fields for the UI
            return {
                "admin_result": {
                    "success": True,
                    "needs_info": True,
                    "operation": analysis.operation,
                    "operation_title": analysis.operation_title,
                    "params": params_dict,
                    "input_fields": [f.model_dump() for f in analysis.input_fields],
                    "guidance_message": analysis.guidance_message,
                },
                "cluster_context": cluster_info,
            }

        else:  # unclear
            # Can't determine what user wants - show operation picker
            return {
                "admin_result": {
                    "success": True,
                    "unclear": True,
                    "guidance_message": analysis.guidance_message or "What would you like to do?",
                    "available_operations": [
                        {
                            "id": "create_topic",
                            "label": "Create a new topic",
                            "icon": "add",
                        },
                        {
                            "id": "delete_topic",
                            "label": "Delete a topic",
                            "icon": "delete",
                        },
                        {
                            "id": "alter_topic_config",
                            "label": "Modify topic configuration",
                            "icon": "settings",
                        },
                        {
                            "id": "add_partitions",
                            "label": "Add partitions to a topic",
                            "icon": "partition",
                        },
                        {
                            "id": "delete_consumer_group",
                            "label": "Delete a consumer group",
                            "icon": "group",
                        },
                    ],
                },
                "cluster_context": cluster_info,
            }

    except Exception as e:
        logger.error(f"Admin agent error: {e}")
        return {
            "admin_result": {
                "success": False,
                "error": f"Failed to analyze admin request: {str(e)}",
            },
            "error": str(e),
        }


async def execute_confirmed_operation(operation: str, params: dict) -> dict:
    """
    Execute a confirmed admin operation.

    This should only be called after the user has explicitly confirmed the operation.
    """
    logger.info(f"Executing confirmed admin operation: {operation} with params: {params}")

    context = get_cluster_context()

    if context is None:
        return {
            "success": False,
            "error": "No Kafka cluster connected.",
        }

    try:
        result = execute_admin_operation(context, operation, params)
        logger.info(f"Admin operation result: {result}")
        return result
    except Exception as e:
        logger.error(f"Admin operation execution error: {e}")
        return {
            "success": False,
            "error": f"Failed to execute operation: {str(e)}",
        }


def execute_admin_operation(context, operation: str, params: dict) -> dict:
    """Execute the specified admin operation."""
    operation_map = {
        "delete_topic": lambda: context.delete_topic(
            topic_name=params.get("topic_name"),
        ),
        "create_topic": lambda: context.create_topic(
            topic_name=params.get("topic_name"),
            num_partitions=params.get("num_partitions", 1),
            replication_factor=params.get("replication_factor", 1),
            config=params.get("config"),
        ),
        "describe_topic": lambda: context.describe_topic(
            topic_name=params.get("topic_name"),
        ),
        "alter_topic_config": lambda: context.alter_topic_config(
            topic_name=params.get("topic_name"),
            config_updates={params.get("config_key"): params.get("config_value")}
            if params.get("config_key")
            else {},
        ),
        "delete_consumer_group": lambda: context.delete_consumer_group(
            group_id=params.get("group_id"),
        ),
        "add_partitions": lambda: context.add_partitions(
            topic_name=params.get("topic_name"),
            new_total_partitions=params.get("new_total_partitions"),
        ),
        "describe_consumer_group": lambda: context.describe_consumer_group(
            group_id=params.get("group_id"),
        ),
    }

    if operation not in operation_map:
        return {
            "success": False,
            "operation": operation,
            "error": f"Unknown operation: {operation}",
        }

    # Validate required parameters
    required_params = {
        "delete_topic": ["topic_name"],
        "create_topic": ["topic_name"],
        "describe_topic": ["topic_name"],
        "alter_topic_config": ["topic_name", "config_key", "config_value"],
        "delete_consumer_group": ["group_id"],
        "add_partitions": ["topic_name", "new_total_partitions"],
        "describe_consumer_group": ["group_id"],
    }

    missing = [p for p in required_params.get(operation, []) if not params.get(p)]
    if missing:
        return {
            "success": False,
            "operation": operation,
            "error": f"Missing required parameters: {', '.join(missing)}",
        }

    return operation_map[operation]()
