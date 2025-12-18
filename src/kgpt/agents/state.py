"""Agent state definitions for the multi-agent system."""

from typing import Annotated, TypedDict

from langchain_core.documents import Document
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """State shared between all agents in the graph."""

    # The user's original question
    question: str

    # Decomposed sub-goals from the router
    sub_goals: list[str]

    # Routing decisions
    needs_cluster_context: bool
    needs_retrieval: bool
    needs_web_search: bool  # Whether to search the web for current info
    needs_admin_operation: bool  # Whether this is an admin operation request
    route: str  # "retrieval", "kafka", "admin", "both", or "direct"

    # Admin operation details (parsed from question)
    admin_operation: dict | None  # {"type": "delete_topic", "params": {...}}

    # Retrieved documents from the retrieval agent
    retrieved_docs: list[Document]

    # Web search results from Exa
    web_results: list[dict]

    # Cluster context from the Kafka agent (if applicable)
    cluster_context: dict | None

    # Admin operation result (if an operation was executed)
    admin_result: dict | None

    # The final synthesized answer
    answer: str

    # Source citations (now includes both doc and web sources)
    citations: list[dict]

    # Conversation history (for context)
    messages: Annotated[list, add_messages]

    # Error message if something went wrong
    error: str | None


class RouterDecision(TypedDict):
    """Decision output from the router agent."""

    route: str  # "retrieval", "kafka", "both", or "direct"
    sub_goals: list[str]
    needs_web_search: bool
    reasoning: str
