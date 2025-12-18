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

    This endpoint dynamically reads the actual LangGraph structure from the
    graph_builder module to ensure the visualization matches the real code.
    """
    from kgpt.agents.kafka_agent import get_cluster_context
    from kgpt.agents.orchestrator.graph_builder import create_agent_graph

    # Check if cluster is connected
    cluster_connected = get_cluster_context() is not None

    # Get the actual graph structure from LangGraph
    graph = create_agent_graph()

    # Node metadata - maps node names to UI display info
    # These match the actual nodes defined in graph_builder.py
    node_metadata = {
        "router": {
            "label": "Router",
            "description": "Analyzes query intent and determines which agents to invoke",
            "icon": "M13 10V3L4 14h7v7l9-11h-7z",
            "color": "text-violet-400",
        },
        "kafka": {
            "label": "Kafka Context",
            "description": "Retrieves live cluster metadata (topics, configs, consumer groups)",
            "icon": "M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10",
            "color": "text-emerald-400",
        },
        "retrieval": {
            "label": "Retrieval",
            "description": "Searches documentation using query expansion, hybrid search, and reranking",
            "icon": "M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z",
            "color": "text-blue-400",
        },
        "admin": {
            "label": "Admin",
            "description": "Analyzes and prepares admin operations (create/delete topics, alter configs)",
            "icon": "M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z",
            "color": "text-amber-400",
        },
        "synthesis": {
            "label": "Synthesis",
            "description": "Generates the final answer using LLM with retrieved context",
            "icon": "M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z",
            "color": "text-emerald-400",
        },
    }

    # Dynamically build nodes from the actual graph
    # The graph.nodes gives us the actual node names
    actual_nodes = list(graph.nodes.keys())
    nodes = []
    for node_name in actual_nodes:
        meta = node_metadata.get(
            node_name,
            {
                "label": node_name.title(),
                "description": f"{node_name} agent",
                "icon": "M12 6v6m0 0v6m0-6h6m-6 0H6",
                "color": "text-surface-400",
            },
        )
        nodes.append(
            AgentGraphNode(
                name=node_name,
                label=meta["label"],
                description=meta["description"],
                icon=meta["icon"],
                color=meta["color"],
            )
        )

    # Build edges from the actual graph structure
    # For LangGraph, we can introspect the edges
    edges = []

    # Add START edge (entry point)
    edges.append(
        AgentGraphEdge(
            from_node="START",
            to_node="router",
            condition=None,
        )
    )

    # Router has conditional edges - document the routing logic
    router_conditions = {
        "retrieval": "route == 'retrieval' (docs only)",
        "kafka": "route == 'both' (cluster context + docs)",
        "admin": "route == 'admin' (cluster operation)",
        "synthesis": "route == 'direct' or 'help' (simple response)",
    }

    for target, condition in router_conditions.items():
        if target in actual_nodes:
            edges.append(
                AgentGraphEdge(
                    from_node="router",
                    to_node=target,
                    condition=condition,
                )
            )

    # Add fixed edges based on actual graph_builder.py:
    # - retrieval -> synthesis
    # - admin -> synthesis
    # - kafka -> retrieval (kafka is only for "both" route, always goes to retrieval)
    # - synthesis -> END
    if "retrieval" in actual_nodes:
        edges.append(
            AgentGraphEdge(
                from_node="retrieval",
                to_node="synthesis",
                condition=None,
            )
        )

    if "admin" in actual_nodes:
        edges.append(
            AgentGraphEdge(
                from_node="admin",
                to_node="synthesis",
                condition=None,
            )
        )

    if "kafka" in actual_nodes:
        edges.append(
            AgentGraphEdge(
                from_node="kafka",
                to_node="retrieval",
                condition="always (provides context for docs)",
            )
        )

    edges.append(
        AgentGraphEdge(
            from_node="synthesis",
            to_node="END",
            condition=None,
        )
    )

    description = f"""Multi-agent orchestration using LangGraph.

The system uses a state graph to coordinate specialized agents:
- Router analyzes intent and determines the execution path
- Kafka agent fetches live cluster metadata ({("connected" if cluster_connected else "not connected")})
- Retrieval agent searches documentation using RAG pipeline
- Admin agent prepares cluster operations for user confirmation
- Synthesis agent generates the final answer

The graph supports multiple execution paths:
1. **Documentation-only**: router -> retrieval -> synthesis
2. **Combined**: router -> kafka -> retrieval -> synthesis
3. **Admin**: router -> admin -> synthesis
4. **Direct**: router -> synthesis (for greetings/help)
"""

    return AgentGraphInfo(
        nodes=nodes,
        edges=edges,
        entry_point="router",
        description=description,
    )
