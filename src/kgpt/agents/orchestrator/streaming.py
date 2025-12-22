"""Streaming query execution with agent activity visibility."""

from collections.abc import AsyncGenerator
from datetime import datetime

from langchain_core.messages import AIMessage, HumanMessage
from loguru import logger

from kgpt.agents.state import AgentState


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
        # Legacy fields initialized to avoid errors if referenced
        "sub_goals": [],
        "needs_cluster_context": False,
        "retrieved_docs": [],
        "web_results": [],
        "cluster_context": None,
        "admin_result": None,
        "error": None,
        "route": "direct",
    }

    citations = []

    yield {"stage": "Thinking..."}

    try:
        # Simulate Router Event (for UI "Pipeline" visualization)
        yield {
            "agent_event": {
                "agent": "router",
                "status": "completed",
                "description": "Routing to appropriate agents",
                "timestamp": datetime.now().isoformat(),
                "result": {"route": "dynamic"},
            }
        }

        has_emitted_synthesis = False

        # Use astream_events to catch real-time execution details
        # version="v1" required for reliable formatting in current LangGraph versions
        async for event in compiled_graph.astream_events(initial_state, version="v1"):
            kind = event["event"]
            name = event["name"]
            data = event["data"]

            # Log ALL events for debugging
            logger.info(f"Event: kind={kind}, name={name}")

            # Tool Execution Start
            if kind == "on_tool_start":
                tool_name = name
                agent_type = "unknown"
                description = f"Running {tool_name}"

                # Map tools to "agents" for frontend UI compatibility
                if "topic" in tool_name or "cluster" in tool_name or "consumer" in tool_name:
                    agent_type = "kafka"
                    description = f"Executing {tool_name}..."
                elif "search_knowledge" in tool_name:
                    agent_type = "retrieval"
                    description = "Searching documentation..."
                elif "search_web" in tool_name:
                    agent_type = "web_search"
                    description = "Searching the web..."

                yield {
                    "agent_event": {
                        "agent": agent_type,
                        "status": "started",
                        "description": description,
                        "timestamp": datetime.now().isoformat(),
                    }
                }

            # Tool Execution End
            elif kind == "on_tool_end":
                tool_name = name
                output = data.get("output")

                # Check for string output with embedded artifacts
                artifacts = []

                # If it's a ToolMessage (standard for langchain tool events), get the content
                if hasattr(output, "content"):
                    output_str = str(output.content)
                else:
                    output_str = str(output)

                output_content = output_str

                if "__ARTIFACTS__" in output_str:
                    try:
                        import json

                        # Robust splitting - take the last occurrence if somehow multiple exist
                        parts = output_str.split("__ARTIFACTS__")
                        if len(parts) >= 2:
                            content_part = "__ARTIFACTS__".join(parts[:-1])
                            artifacts_part = parts[-1].strip()
                            output_content = content_part.strip()
                            artifacts = json.loads(artifacts_part)
                        else:
                            pass  # Artifact tag found but split failed
                    except Exception as e:
                        logger.error(f"Failed to parse artifacts: {e}")

                agent_type = "unknown"
                if "topic" in tool_name or "cluster" in tool_name or "consumer" in tool_name:
                    agent_type = "kafka"
                elif "search_knowledge" in tool_name:
                    agent_type = "retrieval"
                    if artifacts:
                        citations.extend(artifacts)
                        yield {"citations": citations}
                elif "search_web" in tool_name:
                    agent_type = "web_search"
                    if artifacts:
                        citations.extend(artifacts)
                        yield {"citations": citations}

                yield {
                    "agent_event": {
                        "agent": agent_type,
                        "status": "completed",
                        "result": {
                            "output": str(output_content)[:200] + "..."
                            if output_content
                            else "Done"
                        },  # Summary
                        "timestamp": datetime.now().isoformat(),
                    }
                }

                # If we got a real object back (like dict from Kafka tools), we can show it
                if isinstance(output, dict) and agent_type == "kafka":
                    # Frontend might expect specific "admin_result" or "cluster_context"
                    # We can map it to "admin_result" for detailed cards
                    yield {"admin_result": output}

            # LLM Streaming (Content)
            elif kind == "on_chat_model_stream":
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

                chunk = data.get("chunk")
                # Log chunk details
                if chunk:
                    logger.info(
                        f"Chunk: content='{chunk.content[:50] if chunk.content else ''}', tool_calls={getattr(chunk, 'tool_calls', [])}"
                    )
                if chunk and chunk.content:
                    # If we are getting content, we are likely in the final answer retrieval phase
                    # unless it's a thought trace (which is rare to stream as content in standard chat models)
                    yield chunk.content

        # Mark synthesis as complete
        if has_emitted_synthesis:
            yield {
                "agent_event": {
                    "agent": "synthesis",
                    "status": "completed",
                    "timestamp": datetime.now().isoformat(),
                }
            }

        # Final Citations
        if citations:
            yield {"citations": citations}

        yield {"done": True}

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Streaming error: {error_msg}")
        yield f"Error: {error_msg}"
        yield {"done": True}
