"""Streaming query execution with agent activity visibility."""

from collections.abc import AsyncGenerator
from datetime import datetime

from langchain_core.messages import AIMessage, HumanMessage
from loguru import logger

from kgpt.agents.graph import AgentState
from kgpt.tools.kafka_tools import get_kafka_tools

# Get set of Kafka tool names for robust matching
KAFKA_TOOL_NAMES = {t.name for t in get_kafka_tools()}


def _resolve_agent_type(tool_name: str) -> tuple[str, str]:
    """Resolve agent type and description based on tool name."""
    if tool_name in KAFKA_TOOL_NAMES:
        return "kafka", f"Running {tool_name}"

    if tool_name == "enhance_query":
        return "retrieval", "Formulating search strategy..."

    if tool_name == "search":
        return "retrieval", "Searching Knowledge Base & Web..."

    return "unknown", f"Running {tool_name}"


def _parse_artifacts(output_str: str) -> tuple[str, list]:
    """Extract embedded artifacts from tool output."""
    if "__ARTIFACTS__" not in output_str:
        return output_str, []

    try:
        import json

        parts = output_str.split("__ARTIFACTS__")
        if len(parts) >= 2:
            content_part = "__ARTIFACTS__".join(parts[:-1])
            artifacts_part = parts[-1].strip()
            return content_part.strip(), json.loads(artifacts_part)
    except Exception as e:
        logger.error(f"Failed to parse artifacts: {e}")

    return output_str, []


async def query_stream_with_stages(
    question: str,
    chat_history: list | None = None,
    compiled_graph=None,
) -> AsyncGenerator[str | dict, None]:
    """
    Process a question with streaming output and trace events.
    Uses LangGraph astream_events to capture real-time tool execution.
    """
    if not compiled_graph:
        logger.error("No compiled graph provided to streaming")
        yield "Error: Agent configuration missing."
        return

    # Initialize state
    messages = []
    if chat_history:
        for msg in chat_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=question))

    initial_state: AgentState = {
        "question": question,
        "messages": messages,
        "trace_events": [],
        "citations": [],
        "answer": "",
        "error": None,
    }

    citations = []
    yield {"stage": "Thinking..."}

    try:
        has_emitted_synthesis = False

        # version="v1" required for stable LangGraph streaming
        async for event in compiled_graph.astream_events(initial_state, version="v1"):
            kind = event["event"]
            name = event["name"]
            data = event["data"]

            # 1. Tool Start
            if kind == "on_tool_start":
                agent_type, description = _resolve_agent_type(name)

                # Append input details if available
                tool_input = data.get("input", {})
                if isinstance(tool_input, dict) and tool_input:
                    description += f" ({', '.join([f'{k}={v}' for k, v in tool_input.items()])})"

                yield {
                    "agent_event": {
                        "agent": agent_type,
                        "status": "started",
                        "description": description,
                        "timestamp": datetime.now().isoformat(),
                    }
                }

            # 2. Tool End
            elif kind == "on_tool_end":
                output = data.get("output")
                output_str = str(output.content) if hasattr(output, "content") else str(output)

                content, artifacts = _parse_artifacts(output_str)
                agent_type, _ = _resolve_agent_type(name)

                # Add citations if this was a retrieval tool
                if agent_type == "retrieval" and artifacts:
                    citations.extend(artifacts)
                    yield {"citations": citations}

                yield {
                    "agent_event": {
                        "agent": agent_type,
                        "status": "completed",
                        "result": {
                            "tool": name,
                            "output": content[:500] + ("..." if len(content) > 500 else ""),
                            "artifact_count": len(artifacts),
                        },
                        "timestamp": datetime.now().isoformat(),
                    }
                }

                # For Kafka tools, return the raw object for detailed UI cards
                if agent_type == "kafka" and isinstance(output, dict):
                    yield {"admin_result": output}

            # 3. LLM Content Stream
            elif kind == "on_chat_model_stream":
                chunk = data.get("chunk")
                if chunk and chunk.content:
                    if not has_emitted_synthesis:
                        has_emitted_synthesis = True
                        yield {
                            "agent_event": {
                                "agent": "synthesis",
                                "status": "started",
                                "description": "Synthesizing answer...",
                                "timestamp": datetime.now().isoformat(),
                            }
                        }
                    yield chunk.content

        # Final Synthesis Completion
        if has_emitted_synthesis:
            yield {
                "agent_event": {
                    "agent": "synthesis",
                    "status": "completed",
                    "result": {"output": "Response generated"},
                    "timestamp": datetime.now().isoformat(),
                }
            }

        if citations:
            yield {"citations": citations}

        yield {"done": True}

    except Exception as e:
        logger.error(f"Streaming error: {e}")
        yield f"Error: {str(e)}"
        yield {"done": True}
