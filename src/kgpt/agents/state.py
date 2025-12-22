"""Agent state definitions for the multi-agent system."""

from typing import Annotated, TypedDict

from langchain_core.documents import Document
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """State shared between all agents in the graph."""

    # The user's original question
    question: str

    # Message history (standard ReAct)
    messages: Annotated[list, add_messages]

    # --- Core Output Fields ---
    # The final synthesized answer
    answer: str
    # Source citations
    citations: list[dict]
    # Error message if something went wrong
    error: str | None
    # Educational mode trace events
    trace_events: list[dict]

    # --- Legacy / Future Use (Complex Routing) ---
    # These fields are preserved for future multi-agent expansion
    # but are not actively used by the current simple Agent->Tools graph.
    sub_goals: list[str]
    needs_cluster_context: bool
    needs_retrieval: bool
    needs_web_search: bool
    needs_admin_operation: bool
    route: str
    admin_operation: dict | None
    retrieved_docs: list[Document]
    web_results: list[dict]
    cluster_context: dict | None
    admin_result: dict | None
    help_response: dict | None
    suggested_prompts: list[str]


class RouterDecision(TypedDict):
    """Decision output from the router agent."""

    route: str  # "retrieval", "kafka", "both", or "direct"
    sub_goals: list[str]
    needs_web_search: bool
    reasoning: str
