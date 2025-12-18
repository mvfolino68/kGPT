"""LangGraph orchestration for the multi-agent system."""

from collections.abc import AsyncGenerator

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, StateGraph
from loguru import logger

from kgpt.agents.admin import admin_node
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
        START -> router -> [retrieval | kafka | admin | synthesis] -> ... -> synthesis -> END

    Routes:
    - "retrieval": docs only -> retrieval -> validation -> synthesis
    - "kafka": cluster only -> kafka -> synthesis (skip docs!)
    - "admin": admin operation -> admin -> synthesis
    - "both": cluster + docs -> kafka -> retrieval -> validation -> synthesis
    - "direct": simple response -> synthesis
    """
    # Create the graph
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("router", router_node)
    graph.add_node("retrieval", retrieval_node)
    graph.add_node("kafka", kafka_node)
    graph.add_node("admin", admin_node)
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
            "admin": "admin",
            "synthesis": "synthesis",  # Direct route
        },
    )

    # Retrieval -> Validation
    graph.add_edge("retrieval", "validation")

    # Admin -> Synthesis (admin operations go directly to synthesis)
    graph.add_edge("admin", "synthesis")

    # Kafka -> Retrieval (if needs_retrieval) or Synthesis (if kafka-only)
    def kafka_next_node(state: AgentState) -> str:
        """Determine next node after kafka based on routing."""
        if state.get("needs_retrieval"):
            return "retrieval"
        return "synthesis"

    graph.add_conditional_edges(
        "kafka",
        kafka_next_node,
        {
            "retrieval": "retrieval",
            "synthesis": "synthesis",
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
            "needs_retrieval": True,  # Default to retrieval
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

        try:
            from langchain_core.prompts import ChatPromptTemplate

            from kgpt.agents.admin import admin_node
            from kgpt.agents.synthesis import (
                ADMIN_SYNTHESIS_SYSTEM_PROMPT,
                ADMIN_SYNTHESIS_USER_PROMPT,
                SYNTHESIS_SYSTEM_PROMPT,
                SYNTHESIS_USER_PROMPT,
                extract_citations,
                format_admin_result,
                format_cluster_context,
                format_documents,
            )
            from kgpt.llm import get_llm

            # Step 1: Router - determine what we need
            yield {"stage": "Understanding your question..."}
            router_result = await router_node(initial_state)
            state = {**initial_state, **router_result}

            route = state.get("route", "retrieval")
            needs_cluster = state.get("needs_cluster_context", False)
            needs_retrieval = state.get("needs_retrieval", True)
            needs_admin = state.get("needs_admin_operation", False)

            logger.info(
                f"Route: {route}, cluster={needs_cluster}, retrieval={needs_retrieval}, admin={needs_admin}"
            )

            # Handle help route - provide canned response about capabilities
            if route == "help":
                yield {"stage": ""}
                help_response = """## 🚀 What I Can Do

I'm your Kafka assistant! Here's what I can help you with:

### 📊 Query & Explore
- **Check cluster status** - View brokers, topics, and consumer groups
- **List topics** - See all topics with their partition counts
- **Describe topics** - Get detailed topic configuration
- **Consumer lag** - Check consumer group lag and offsets

### ⚡ Admin Operations
I can execute these operations directly on your connected cluster:

| Operation | Example Command |
|-----------|-----------------|
| **Create topic** | "Create a topic called orders with 3 partitions" |
| **Delete topic** | "Delete the topic named test-topic" |
| **Alter config** | "Set retention.ms to 604800000 for topic orders" |
| **Add partitions** | "Increase partitions to 6 for topic events" |
| **Delete consumer group** | "Delete consumer group my-consumer-group" |

### 📚 Documentation
- Ask about Kafka concepts, best practices, and configurations
- Get help with producers, consumers, and Streams
- Learn about security, monitoring, and troubleshooting

### 💡 Tips
- Connect to a cluster first in the **Cluster** page
- Use natural language - I understand requests like "delete my orders topic"
- Ask follow-up questions for more details

**Try asking:** "List all topics in my cluster" or "Create a topic called events with 5 partitions"
"""
                # Stream the help response character by character for nice effect
                for char in help_response:
                    yield char

                yield {"citations": []}
                return

            # Handle admin operations
            if needs_admin and not state.get("error"):
                yield {"stage": "Analyzing your request..."}
                admin_result = await admin_node(state)
                state = {**state, **admin_result}

                # Send cluster context and admin result to frontend
                if state.get("cluster_context"):
                    yield {"cluster_context": state["cluster_context"]}
                if state.get("admin_result"):
                    yield {"admin_result": state["admin_result"]}

                # Check the status of the admin analysis
                admin_res = state.get("admin_result", {})
                is_pending = admin_res.get("pending", False)
                needs_info = admin_res.get("needs_info", False)
                is_unclear = admin_res.get("unclear", False)
                has_error = admin_res.get("error")

                # For structured UI cards (needs_info, unclear, pending), we don't need
                # to generate text - the cards handle the UI. Just clear the stage.
                if needs_info or is_unclear or is_pending:
                    yield {"stage": ""}
                    yield {"citations": []}
                    return

                # For errors, generate a helpful message
                if has_error:
                    yield {"stage": ""}
                    yield {"citations": []}
                    return

                # Otherwise (shouldn't happen often), generate a response
                yield {"stage": "Generating response..."}
                admin_section = format_admin_result(admin_res)
                cluster_section = format_cluster_context(state.get("cluster_context"))

                llm = get_llm(streaming=True)
                prompt = ChatPromptTemplate.from_messages(
                    [
                        ("system", ADMIN_SYNTHESIS_SYSTEM_PROMPT),
                        ("human", ADMIN_SYNTHESIS_USER_PROMPT),
                    ]
                )

                chain = prompt | llm

                async for chunk in chain.astream(
                    {
                        "question": state["question"],
                        "admin_result": admin_section,
                        "cluster_section": cluster_section,
                    }
                ):
                    if hasattr(chunk, "content") and chunk.content:
                        yield chunk.content

                yield {"citations": []}
                return

            # Step 2: Kafka context (if needed)
            if needs_cluster and not state.get("error"):
                yield {"stage": "Fetching cluster info..."}
                kafka_result = await kafka_node(state)
                state = {**state, **kafka_result}

                # Send cluster context to frontend
                if state.get("cluster_context"):
                    yield {"cluster_context": state["cluster_context"]}

            # Step 3: Retrieval (only if needed!)
            if needs_retrieval and not state.get("error"):
                yield {"stage": "Searching documentation..."}
                retrieval_result = await retrieval_node(state)
                state = {**state, **retrieval_result}

                # Step 4: Validation (only if we retrieved docs)
                if state.get("retrieved_docs"):
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

            # Yield final citations (only if we have docs)
            citations = extract_citations(docs) if docs else []
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
