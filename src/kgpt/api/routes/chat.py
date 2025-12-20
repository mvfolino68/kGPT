"""Chat API routes with SSE streaming support."""

import json
import time
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import BaseModel

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


# ============================================================================
# Agent Graph Structure (Educational)
# ============================================================================


class AgentGraphNode(BaseModel):
    """Represents a node in the agent graph."""

    name: str
    label: str
    description: str
    icon: str
    color: str


class AgentGraphEdge(BaseModel):
    """Represents an edge in the agent graph."""

    from_node: str
    to_node: str
    condition: str | None = None


class AgentGraphInfo(BaseModel):
    """Complete agent graph structure information."""

    nodes: list[AgentGraphNode]
    edges: list[AgentGraphEdge]
    entry_point: str
    description: str


@router.get("/graph", response_model=AgentGraphInfo)
async def get_agent_graph() -> AgentGraphInfo:
    """
    Get the structure of the multi-agent graph.
    """
    from kgpt.services.kafka import get_kafka_service

    # Check if cluster is connected
    service = get_kafka_service()
    cluster_connected = service.config is not None

    # Define the ReAct graph structure
    nodes = [
        AgentGraphNode(
            name="agent",
            label="Agent",
            description="Core ReAct agent that reasons and calls tools",
            icon="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z",
            color="text-violet-400",
        ),
        AgentGraphNode(
            name="tools",
            label="Tools",
            description="Execution of Kafka operations and search tools",
            icon="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z",
            color="text-emerald-400",
        ),
    ]

    edges = [
        AgentGraphEdge(from_node="START", to_node="agent", condition=None),
        AgentGraphEdge(from_node="agent", to_node="tools", condition="calls tool"),
        AgentGraphEdge(from_node="tools", to_node="agent", condition="returns result"),
        AgentGraphEdge(from_node="agent", to_node="END", condition="final answer"),
    ]

    description = f"""ReAct Agent Architecture.

The system uses a flexible reasoning loop:
- **Agent**: The core LLM that plans actions and calls tools.
- **Tools**: A suite of capabilities including Kafka operations ({("connected" if cluster_connected else "not connected")}), documentation search, and web search.

The agent loops between reasoning and tool execution until it arrives at a final answer.
"""

    return AgentGraphInfo(
        nodes=nodes,
        edges=edges,
        entry_point="agent",
        description=description,
    )
