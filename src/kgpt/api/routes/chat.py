"""Chat API routes with SSE streaming support."""

import json
import time
import uuid
from collections.abc import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger

from kgpt.api.schemas import (
    ChatRequest,
    ChatResponse,
    ChatSession,
    ChatSessionMessage,
    ChatSessionsListResponse,
    ChatSessionWithMessages,
    CreateSessionRequest,
    UpdateSessionRequest,
)
from kgpt.db.database import get_db

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def send_message(request: ChatRequest) -> ChatResponse:
    """
    Send a chat message and get a complete response.

    This endpoint waits for the full response before returning.
    For streaming responses, use GET /chat/stream.
    """
    from kgpt.agents import get_orchestrator

    orchestrator = get_orchestrator()

    # Convert history to the format expected by orchestrator
    chat_history = [{"role": msg.role, "content": msg.content} for msg in request.history]

    try:
        result = await orchestrator.query(request.message, chat_history)
        return ChatResponse(
            answer=result.get("answer", "I couldn't generate a response."),
            citations=result.get("citations", []),
            error=result.get("error"),
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return ChatResponse(
            answer=f"I encountered an error: {str(e)}",
            citations=[],
            error=str(e),
        )


def generate_suggested_actions(
    message: str, cluster_context: dict | None = None
) -> list[dict]:
    """Generate contextual suggested actions based on the query and cluster state."""
    actions = []
    message_lower = message.lower()

    # Cluster-related suggestions
    if cluster_context:
        topics = cluster_context.get("topics", [])
        consumer_groups = cluster_context.get("consumer_groups", [])

        if "topic" in message_lower and topics:
            # Suggest exploring specific topics
            if len(topics) > 0:
                actions.append({
                    "id": "describe-topic",
                    "label": f"Describe topic '{topics[0]}'",
                    "type": "query",
                    "value": f"Describe the configuration of topic {topics[0]}",
                    "icon": "📋",
                })
        if "consumer" in message_lower or "lag" in message_lower:
            if consumer_groups:
                actions.append({
                    "id": "check-lag",
                    "label": "Check consumer lag",
                    "type": "query",
                    "value": "Show consumer group lag for all groups",
                    "icon": "⏱️",
                })
        if "cluster" in message_lower or "status" in message_lower:
            actions.append({
                "id": "list-topics",
                "label": "List all topics",
                "type": "query",
                "value": "List all topics with their partition counts",
                "icon": "📋",
            })

    # Documentation-related suggestions
    if "producer" in message_lower:
        actions.append({
            "id": "producer-config",
            "label": "Producer configurations",
            "type": "query",
            "value": "What are the most important producer configurations?",
            "icon": "⚙️",
        })
    if "consumer" in message_lower and "lag" not in message_lower:
        actions.append({
            "id": "consumer-config",
            "label": "Consumer configurations",
            "type": "query",
            "value": "What are the most important consumer configurations?",
            "icon": "⚙️",
        })

    return actions[:3]  # Limit to 3 suggestions


async def generate_sse_stream(
    message: str, history: list[dict], session_id: str | None = None
) -> AsyncGenerator[str, None]:
    """Generate SSE events for streaming chat response with thinking stages."""
    from kgpt.agents import get_orchestrator

    orchestrator = get_orchestrator()
    response_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
    created = int(time.time())
    full_response = ""
    citations = []
    cluster_context = None

    # Save user message to session if provided
    if session_id:
        db = get_db()
        db.add_chat_message(session_id, "user", message)

    try:
        # Send initial thinking stage
        yield f"data: {json.dumps({'stage': 'Analyzing query...'})}\n\n"

        # Use the streaming query method with stage updates
        async for chunk in orchestrator.query_stream_with_stages(message, history):
            if isinstance(chunk, dict):
                # Handle stage updates
                if chunk.get("stage"):
                    yield f"data: {json.dumps({'stage': chunk['stage']})}\n\n"
                    continue

                # Handle cluster context
                if chunk.get("cluster_context"):
                    cluster_context = chunk["cluster_context"]
                    yield f"data: {json.dumps({'cluster_context': cluster_context})}\n\n"
                    continue

                # Final chunk with citations
                if chunk.get("citations"):
                    citations = chunk["citations"]

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
                actions = generate_suggested_actions(message, cluster_context)
                if actions:
                    yield f"data: {json.dumps({'actions': actions})}\n\n"

                yield "data: [DONE]\n\n"

                # Save assistant response to session
                if session_id and full_response:
                    db = get_db()
                    db.add_chat_message(session_id, "assistant", full_response, citations)
            else:
                # Regular text chunk
                full_response += chunk
                event = {
                    "id": response_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": "kgpt",
                    "choices": [{"index": 0, "delta": {"content": chunk}, "finish_reason": None}],
                }
                yield f"data: {json.dumps(event)}\n\n"

    except Exception as e:
        logger.error(f"Streaming error: {e}")
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


class ChatStreamRequest(ChatRequest):
    """Request for streaming chat with optional session persistence."""

    session_id: str | None = None


@router.post("/stream")
async def stream_message(request: ChatStreamRequest) -> StreamingResponse:
    """
    Stream a chat response using Server-Sent Events (SSE).

    If session_id is provided, messages will be persisted to the database.

    Events:
    - type: 'token' - A chunk of the response text
    - type: 'citations' - Source citations
    - type: 'done' - Stream complete
    - type: 'error' - An error occurred
    """
    chat_history = [{"role": msg.role, "content": msg.content} for msg in request.history]

    return StreamingResponse(
        generate_sse_stream(request.message, chat_history, request.session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ============================================================================
# Chat History / Session Management
# ============================================================================


@router.get("/sessions", response_model=ChatSessionsListResponse)
async def list_sessions() -> ChatSessionsListResponse:
    """List all chat sessions."""
    db = get_db()
    sessions = db.get_chat_sessions()
    return ChatSessionsListResponse(
        sessions=[ChatSession(**s) for s in sessions],
        total=len(sessions),
    )


@router.post("/sessions", response_model=ChatSession)
async def create_session(request: CreateSessionRequest) -> ChatSession:
    """Create a new chat session."""
    db = get_db()
    session_id = db.create_chat_session(title=request.title)
    session = db.get_chat_session(session_id)
    if not session:
        raise HTTPException(status_code=500, detail="Failed to create session")
    return ChatSession(**session)


@router.get("/sessions/{session_id}", response_model=ChatSessionWithMessages)
async def get_session(session_id: str) -> ChatSessionWithMessages:
    """Get a chat session with all its messages."""
    db = get_db()
    session = db.get_chat_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = db.get_chat_messages(session_id)
    return ChatSessionWithMessages(
        session=ChatSession(**session),
        messages=[ChatSessionMessage(**m) for m in messages],
    )


@router.put("/sessions/{session_id}", response_model=ChatSession)
async def update_session(session_id: str, request: UpdateSessionRequest) -> ChatSession:
    """Update a chat session's title."""
    db = get_db()
    session = db.get_chat_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    db.update_chat_session(session_id, title=request.title)
    updated = db.get_chat_session(session_id)
    return ChatSession(**updated)


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str) -> dict:
    """Delete a chat session and all its messages."""
    db = get_db()
    session = db.get_chat_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    db.delete_chat_session(session_id)
    return {"status": "deleted", "session_id": session_id}


@router.post("/sessions/{session_id}/messages", response_model=ChatSessionMessage)
async def add_message(session_id: str, message: ChatRequest) -> ChatSessionMessage:
    """Add a message to a chat session."""
    db = get_db()
    session = db.get_chat_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Add the user message
    message_id = db.add_chat_message(
        session_id=session_id,
        role="user",
        content=message.message,
    )

    msg = db.get_chat_messages(session_id)[-1]
    return ChatSessionMessage(**msg)


@router.delete("/sessions")
async def clear_all_sessions() -> dict:
    """Delete all chat sessions and messages."""
    db = get_db()
    db.clear_all_chat_history()
    return {"status": "cleared"}
