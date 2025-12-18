"""SSE stream generation for chat responses with agent activity."""

import json
import time
import uuid
from collections.abc import AsyncGenerator

from loguru import logger
from pydantic import BaseModel

from kgpt.db import get_db


class ChatStreamRequest(BaseModel):
    """Request for streaming chat with optional session persistence."""

    message: str
    history: list[dict]
    session_id: str | None = None


async def generate_sse_stream(
    message: str, history: list[dict], session_id: str | None = None
) -> AsyncGenerator[str, None]:
    """Generate SSE events for streaming chat response with agent activity visibility."""
    from kgpt.agents import get_orchestrator
    from kgpt.services import generate_suggested_actions

    orchestrator = get_orchestrator()
    response_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
    created = int(time.time())
    full_response = ""
    citations = []
    cluster_context = None
    admin_result = None
    stream_complete = False

    # Collect agent trace for persistence
    agent_trace: dict = {
        "routing_decision": None,
        "retrieval_results": None,
        "validation_results": None,
        "web_search_results": None,
        "agent_timeline": [],
    }

    # Save user message to session if provided
    if session_id:
        db = get_db()
        db.add_chat_message(session_id, "user", message)

    try:
        # Send initial thinking stage
        yield f"data: {json.dumps({'stage': 'Analyzing query...'})}\n\n"

        # Use the streaming query method with stage updates and agent events
        async for chunk in orchestrator.query_stream_with_stages(message, history):
            if isinstance(chunk, dict):
                # Handle stage updates
                if chunk.get("stage") is not None:
                    yield f"data: {json.dumps({'stage': chunk['stage']})}\n\n"
                    continue

                # Handle agent events
                if chunk.get("agent_event"):
                    event_data = chunk["agent_event"]
                    # Track agent timeline for persistence
                    agent_trace["agent_timeline"].append(event_data)
                    yield f"data: {json.dumps({'agent_event': event_data})}\n\n"
                    continue

                # Handle routing decision
                if chunk.get("routing_decision"):
                    decision_data = chunk["routing_decision"]
                    agent_trace["routing_decision"] = decision_data
                    yield f"data: {json.dumps({'routing_decision': decision_data})}\n\n"
                    continue

                # Handle retrieval results
                if chunk.get("retrieval_results"):
                    retrieval_data = chunk["retrieval_results"]
                    agent_trace["retrieval_results"] = retrieval_data
                    yield f"data: {json.dumps({'retrieval_results': retrieval_data})}\n\n"
                    continue

                # Handle web search results
                if chunk.get("web_results"):
                    web_data = chunk["web_results"]
                    agent_trace["web_search_results"] = web_data
                    yield f"data: {json.dumps({'web_results': web_data})}\n\n"
                    continue

                # Handle cluster context
                if chunk.get("cluster_context"):
                    cluster_context = chunk["cluster_context"]
                    yield f"data: {json.dumps({'cluster_context': cluster_context})}\n\n"
                    continue

                # Handle admin operation result
                if chunk.get("admin_result"):
                    admin_result = chunk["admin_result"]
                    yield f"data: {json.dumps({'admin_result': admin_result})}\n\n"
                    continue

                # Final chunk with citations or end marker
                if chunk.get("citations") is not None or chunk.get("done"):
                    citations = chunk.get("citations", [])

                    # Send citations to frontend (now structured with title, url, type)
                    if citations:
                        yield f"data: {json.dumps({'citations': citations})}\n\n"

                    # Send finish event
                    finish_event = {
                        "id": response_id,
                        "object": "chat.completion.chunk",
                        "created": created,
                        "model": "kgpt",
                        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                    }
                    yield f"data: {json.dumps(finish_event)}\n\n"

                    # Generate and send suggested actions
                    actions = generate_suggested_actions(message, cluster_context, admin_result)
                    if actions:
                        yield f"data: {json.dumps({'actions': actions})}\n\n"

                    yield "data: [DONE]\n\n"

                    # Save assistant response to session with agent trace
                    if session_id and full_response:
                        db = get_db()
                        # Store full citation objects and agent trace for better UX when viewing history
                        # Only save trace if there's meaningful data
                        trace_to_save = (
                            agent_trace
                            if agent_trace.get("agent_timeline")
                            or agent_trace.get("routing_decision")
                            else None
                        )
                        db.add_chat_message(
                            session_id, "assistant", full_response, citations, trace_to_save
                        )

                    # Mark stream as complete and break
                    stream_complete = True
                    break
            else:
                # Regular text chunk - ensure it's ALWAYS a string
                text_chunk = ""

                if isinstance(chunk, str):
                    text_chunk = chunk
                elif isinstance(chunk, (int, float)):
                    text_chunk = str(chunk)
                elif hasattr(chunk, "content"):
                    # Handle AIMessageChunk or similar objects
                    content = chunk.content
                    if isinstance(content, str):
                        text_chunk = content
                    elif isinstance(content, list):
                        # Handle content block format [{"type": "text", "text": "..."}]
                        texts = []
                        for item in content:
                            if isinstance(item, str):
                                texts.append(item)
                            elif isinstance(item, dict):
                                if "text" in item and isinstance(item["text"], str):
                                    texts.append(item["text"])
                                elif "content" in item and isinstance(item["content"], str):
                                    texts.append(item["content"])
                        text_chunk = "".join(texts)
                    elif isinstance(content, dict):
                        if "text" in content and isinstance(content["text"], str):
                            text_chunk = content["text"]
                        elif "content" in content and isinstance(content["content"], str):
                            text_chunk = content["content"]

                if not text_chunk:
                    continue

                full_response += text_chunk
                event = {
                    "id": response_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": "kgpt",
                    "choices": [
                        {"index": 0, "delta": {"content": text_chunk}, "finish_reason": None}
                    ],
                }
                yield f"data: {json.dumps(event)}\n\n"

        # If stream completed normally but loop ended without explicit citations event
        if not stream_complete:
            logger.warning("Stream ended without sending [DONE] - sending now")
            finish_event = {
                "id": response_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": "kgpt",
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
            }
            yield f"data: {json.dumps(finish_event)}\n\n"
            yield "data: [DONE]\n\n"

            # Save assistant response to session if not already saved
            if session_id and full_response:
                db = get_db()
                trace_to_save = (
                    agent_trace
                    if agent_trace.get("agent_timeline") or agent_trace.get("routing_decision")
                    else None
                )
                db.add_chat_message(session_id, "assistant", full_response, [], trace_to_save)

    except Exception as e:
        logger.error(f"Streaming error: {e}", exc_info=True)
        error_msg = f"Error: {str(e)}"
        error_event = {
            "id": response_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": "kgpt",
            "choices": [{"index": 0, "delta": {"content": error_msg}, "finish_reason": "stop"}],
        }
        yield f"data: {json.dumps(error_event)}\n\n"
        yield "data: [DONE]\n\n"

        if session_id:
            db = get_db()
            db.add_chat_message(session_id, "assistant", full_response + error_msg)
