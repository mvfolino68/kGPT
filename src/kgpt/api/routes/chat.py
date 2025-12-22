"""Chat API routes with SSE streaming support."""

import json
import time
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger

from kgpt.api.schemas import (
    AdminOperationRequest,
    AdminOperationResponse,
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
from kgpt.services import ChatStreamRequest, generate_sse_stream

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
    # ChatStreamRequest.history is list[dict], handle accordingly
    chat_history = [
        {"role": msg.get("role", ""), "content": msg.get("content", "")} for msg in request.history
    ]

    async def error_wrapper():
        """Wrapper to catch exceptions during stream generation."""
        try:
            async for chunk in generate_sse_stream(
                request.message, chat_history, request.session_id
            ):
                yield chunk
        except Exception as e:
            logger.error(f"Streaming error in wrapper: {e}", exc_info=True)
            # Send error event
            response_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
            created = int(time.time())
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

    return StreamingResponse(
        error_wrapper(),
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


# ============================================================================
# Admin Operation Execution
# ============================================================================


@router.post("/admin/execute", response_model=AdminOperationResponse)
async def execute_admin_operation(request: AdminOperationRequest) -> AdminOperationResponse:
    """
    Execute a confirmed admin operation.

    This endpoint should only be called after the user has reviewed and confirmed
    the operation details. It will execute the operation on the connected Kafka cluster.
    """
    from kgpt.agents.admin_node import execute_confirmed_operation

    logger.info(f"Executing confirmed admin operation: {request.operation}")

    try:
        result = await execute_confirmed_operation(request.operation, request.params)

        # Handle partitions - can be int or list depending on operation
        partitions = result.get("partitions")
        partition_count = result.get("partition_count")

        # For describe_topic, partitions is a list of partition details
        if isinstance(partitions, list):
            partition_count = len(partitions)

        return AdminOperationResponse(
            success=result.get("success", False),
            operation=request.operation,
            message=result.get("message"),
            error=result.get("error"),
            topic=result.get("topic"),
            group_id=result.get("group_id"),
            partitions=partitions,
            partition_count=partition_count,
            replication_factor=result.get("replication_factor"),
            configuration=result.get("configuration"),
            all_configs=result.get("all_configs"),
        )
    except Exception as e:
        logger.error(f"Admin operation execution error: {e}")
        return AdminOperationResponse(
            success=False,
            operation=request.operation,
            error=str(e),
        )
