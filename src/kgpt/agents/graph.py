"""LangGraph orchestration for the multi-agent system."""

from collections.abc import AsyncGenerator

from langchain_core.messages import AIMessage, HumanMessage
from loguru import logger

from kgpt.agents.orchestrator import compile_graph, query_stream_with_stages
from kgpt.agents.state import AgentState


class AgentOrchestrator:
    """High-level orchestrator for the multi-agent system."""

    def __init__(self):
        """Initialize the orchestrator."""
        self._compiled_graph = None

    @property
    def graph(self):
        """Lazy-load the compiled graph."""
        if self._compiled_graph is None:
            self._compiled_graph = compile_graph()
        return self._compiled_graph

    async def query(
        self,
        question: str,
        chat_history: list | None = None,
    ) -> dict:
        """
        Process a question through the agent pipeline.

        Args:
            question: The user's question
            chat_history: Optional chat history for context

        Returns:
            Dict with 'answer' and 'citations'
        """
        logger.info(f"Processing question: {question[:100]}...")

        # Build initial state
        messages = []
        if chat_history:
            for msg in chat_history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                else:
                    messages.append(AIMessage(content=msg["content"]))

        messages.append(HumanMessage(content=question))

        initial_state: AgentState = {
            "question": question,
            "sub_goals": [],
            "needs_cluster_context": False,
            "needs_retrieval": True,
            "needs_admin_operation": False,
            "route": "retrieval",
            "admin_operation": None,
            "retrieved_docs": [],
            "validated_docs": [],
            "cluster_context": None,
            "admin_result": None,
            "answer": "",
            "citations": [],
            "messages": messages,
            "error": None,
        }

        # Run the graph
        try:
            result = await self.graph.ainvoke(initial_state)

            return {
                "answer": result.get("answer", "I couldn't generate an answer."),
                "citations": result.get("citations", []),
                "error": result.get("error"),
            }

        except Exception as e:
            logger.error(f"Agent orchestration error: {e}")
            return {
                "answer": f"I encountered an error processing your question: {str(e)}",
                "citations": [],
                "error": str(e),
            }

    async def query_stream(
        self,
        question: str,
        chat_history: list | None = None,
    ) -> AsyncGenerator[str | dict, None]:
        """
        Process a question with streaming output.

        Yields tokens as they are generated, then a final dict with citations.
        """
        async for chunk in self.query_stream_with_stages(question, chat_history):
            yield chunk

    async def query_stream_with_stages(
        self,
        question: str,
        chat_history: list | None = None,
    ) -> AsyncGenerator[str | dict, None]:
        """
        Process a question with streaming output, stage updates, and agent activity events.

        Yields:
            - {"stage": "..."} for thinking stage updates
            - {"agent_event": {...}} for agent activity (start/complete/error)
            - {"routing_decision": {...}} for routing info
            - {"retrieval_results": {...}} for retrieved docs
            - {"validation_results": {...}} for validation info
            - {"cluster_context": {...}} for cluster info
            - {"admin_result": {...}} for admin operation result
            - str for content tokens
            - {"citations": [...]} for final citations
        """
        async for chunk in query_stream_with_stages(question, chat_history, self.graph):
            yield chunk


# Singleton orchestrator
_orchestrator: AgentOrchestrator | None = None


def get_orchestrator() -> AgentOrchestrator:
    """Get the singleton orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator
