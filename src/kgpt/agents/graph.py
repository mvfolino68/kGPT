"""LangGraph orchestration for the multi-agent system."""

from collections.abc import AsyncGenerator

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, StateGraph
from loguru import logger

from kgpt.agents.kafka_agent import kafka_node
from kgpt.agents.retrieval import retrieval_node
from kgpt.agents.router import route_decision, router_node
from kgpt.agents.state import AgentState
from kgpt.agents.synthesis import synthesis_node
from kgpt.agents.validation import validation_node


def create_agent_graph() -> StateGraph:
    """
    Create the multi-agent graph.

    Graph structure:
        START -> router -> [retrieval | kafka] -> validation -> synthesis -> END

    The router decides whether to:
    - Go to retrieval (documentation search)
    - Go to kafka (cluster context)
    - Go to both (retrieval first, then kafka)
    """
    # Create the graph
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("router", router_node)
    graph.add_node("retrieval", retrieval_node)
    graph.add_node("kafka", kafka_node)
    graph.add_node("validation", validation_node)
    graph.add_node("synthesis", synthesis_node)

    # Set entry point
    graph.set_entry_point("router")

    # Add conditional edges from router
    graph.add_conditional_edges(
        "router",
        route_decision,
        {
            "retrieval": "retrieval",
            "kafka": "kafka",
            "synthesis": "synthesis",  # Direct route on error
        },
    )

    # Retrieval -> Validation
    graph.add_edge("retrieval", "validation")

    # Kafka -> Retrieval (to also get docs) or Validation (if we have docs)
    graph.add_conditional_edges(
        "kafka",
        lambda state: "retrieval" if not state.get("retrieved_docs") else "validation",
        {
            "retrieval": "retrieval",
            "validation": "validation",
        },
    )

    # Validation -> Synthesis
    graph.add_edge("validation", "synthesis")

    # Synthesis -> END
    graph.add_edge("synthesis", END)

    return graph


def compile_graph():
    """Compile the agent graph for execution."""
    graph = create_agent_graph()
    return graph.compile()


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
            "retrieved_docs": [],
            "validated_docs": [],
            "cluster_context": None,
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
        Process a question with streaming output and stage updates.

        Yields:
            - {"stage": "..."} for thinking stage updates
            - {"cluster_context": {...}} for cluster info
            - str for content tokens
            - {"citations": [...]} for final citations
        """
        logger.info(f"Processing question (streaming): {question[:100]}...")

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
            "retrieved_docs": [],
            "validated_docs": [],
            "cluster_context": None,
            "answer": "",
            "citations": [],
            "messages": messages,
            "error": None,
        }

        try:
            from langchain_core.prompts import ChatPromptTemplate

            from kgpt.agents.synthesis import (
                SYNTHESIS_SYSTEM_PROMPT,
                SYNTHESIS_USER_PROMPT,
                extract_citations,
                format_cluster_context,
                format_documents,
            )
            from kgpt.llm import get_llm

            # Step 1: Router
            yield {"stage": "Understanding your question..."}
            router_result = await router_node(initial_state)
            state = {**initial_state, **router_result}

            # Step 2: Kafka context (if needed)
            if state.get("needs_cluster_context") and not state.get("error"):
                yield {"stage": "Fetching cluster info..."}
                kafka_result = await kafka_node(state)
                state = {**state, **kafka_result}

                # Send cluster context to frontend
                if state.get("cluster_context"):
                    yield {"cluster_context": state["cluster_context"]}

            # Step 3: Retrieval
            if not state.get("error"):
                yield {"stage": "Searching documentation..."}
                retrieval_result = await retrieval_node(state)
                state = {**state, **retrieval_result}

            # Step 4: Validation
            yield {"stage": "Validating sources..."}
            validation_result = await validation_node(state)
            state = {**state, **validation_result}

            # Step 5: Streaming synthesis
            yield {"stage": "Generating response..."}
            docs = state.get("validated_docs", []) or state.get("retrieved_docs", [])
            documents_text = format_documents(docs)
            cluster_section = format_cluster_context(state.get("cluster_context"))

            llm = get_llm(streaming=True)
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", SYNTHESIS_SYSTEM_PROMPT),
                    ("human", SYNTHESIS_USER_PROMPT),
                ]
            )

            chain = prompt | llm

            # Stream tokens
            async for chunk in chain.astream(
                {
                    "question": state["question"],
                    "cluster_section": cluster_section,
                    "documents": documents_text,
                }
            ):
                if hasattr(chunk, "content") and chunk.content:
                    yield chunk.content

            # Yield final citations
            citations = extract_citations(docs)
            yield {"citations": citations}

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"Error: {str(e)}"


# Singleton orchestrator
_orchestrator: AgentOrchestrator | None = None


def get_orchestrator() -> AgentOrchestrator:
    """Get the singleton orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator
