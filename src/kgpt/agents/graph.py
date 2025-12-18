"""LangGraph orchestration for the multi-agent system."""

from collections.abc import AsyncGenerator
from typing import Any

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


def extract_text_from_chunk(chunk: Any) -> str | None:
    """
    Extract text content from an LLM streaming chunk.

    Handles various formats:
    - Plain string content
    - List of content blocks [{"type": "text", "text": "..."}] (Claude format)
    - AIMessageChunk with string or list content
    - Other formats that might contain text

    Returns:
        The extracted text string, or None if no text could be extracted.
    """
    # Get the content from the chunk
    if hasattr(chunk, "content"):
        content = chunk.content
    else:
        content = chunk

    # Handle None or empty
    if content is None:
        return None

    # Handle plain strings
    if isinstance(content, str):
        return content if content else None

    # Handle list of content blocks (Claude format)
    if isinstance(content, list):
        texts = []
        for item in content:
            if isinstance(item, dict):
                # {"type": "text", "text": "..."} format
                if "text" in item and isinstance(item["text"], str):
                    texts.append(item["text"])
                # {"content": "..."} format
                elif "content" in item and isinstance(item["content"], str):
                    texts.append(item["content"])
            elif isinstance(item, str):
                texts.append(item)
            # Skip any non-string items that couldn't be extracted
        return "".join(texts) if texts else None

    # Handle dict with text/content keys
    if isinstance(content, dict):
        if "text" in content and isinstance(content["text"], str):
            return content["text"]
        if "content" in content and isinstance(content["content"], str):
            return content["content"]
        # Don't log warning for every dict - just return None
        return None

    # Handle numbers
    if isinstance(content, (int, float)):
        return str(content)

    # Skip unhandled types silently
    return None


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
        import time

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

            # ================================================================
            # Step 1: Router - determine what we need
            # ================================================================
            yield {"stage": "Understanding your question..."}
            yield {
                "agent_event": {
                    "agent": "router",
                    "status": "started",
                    "description": "Analyzing query intent and determining route",
                }
            }

            router_start = time.time()
            router_result = await router_node(initial_state)
            router_duration = int((time.time() - router_start) * 1000)

            state = {**initial_state, **router_result}

            route = state.get("route", "retrieval")
            needs_cluster = state.get("needs_cluster_context", False)
            needs_retrieval = state.get("needs_retrieval", True)
            needs_admin = state.get("needs_admin_operation", False)
            sub_goals = state.get("sub_goals", [])
            reasoning = state.get("reasoning", "")

            # Emit routing decision for educational visibility
            yield {
                "routing_decision": {
                    "route": route,
                    "reasoning": reasoning,
                    "sub_goals": sub_goals,
                    "needs_cluster": needs_cluster,
                    "needs_retrieval": needs_retrieval,
                    "needs_admin": needs_admin,
                }
            }

            yield {
                "agent_event": {
                    "agent": "router",
                    "status": "completed",
                    "duration_ms": router_duration,
                    "result": {"route": route, "sub_goals": sub_goals},
                }
            }

            logger.info(
                f"Route: {route}, cluster={needs_cluster}, retrieval={needs_retrieval}, admin={needs_admin}"
            )

            # Handle help route - provide canned response about capabilities
            if route == "help":
                yield {"stage": ""}
                yield {
                    "agent_event": {
                        "agent": "synthesis",
                        "status": "started",
                        "description": "Generating help response",
                    }
                }

                help_response = """## What I Can Do

I'm your Kafka assistant! Here's what I can help you with:

### Query and Explore
- **Check cluster status** - View brokers, topics, and consumer groups
- **List topics** - See all topics with their partition counts
- **Describe topics** - Get detailed topic configuration
- **Consumer lag** - Check consumer group lag and offsets

### Admin Operations
I can execute these operations directly on your connected cluster:

| Operation | Example Command |
|-----------|-----------------|
| **Create topic** | "Create a topic called orders with 3 partitions" |
| **Delete topic** | "Delete the topic named test-topic" |
| **Alter config** | "Set retention.ms to 604800000 for topic orders" |
| **Add partitions** | "Increase partitions to 6 for topic events" |
| **Delete consumer group** | "Delete consumer group my-consumer-group" |

### Documentation
- Ask about Kafka concepts, best practices, and configurations
- Get help with producers, consumers, and Streams
- Learn about security, monitoring, and troubleshooting

### Tips
- Connect to a cluster first in the **Cluster** page
- Use natural language - I understand requests like "delete my orders topic"
- Ask follow-up questions for more details

**Try asking:** "List all topics in my cluster" or "Create a topic called events with 5 partitions"
"""
                # Stream the help response
                for char in help_response:
                    yield char

                yield {
                    "agent_event": {
                        "agent": "synthesis",
                        "status": "completed",
                    }
                }
                yield {"citations": []}
                return

            # ================================================================
            # Handle admin operations
            # ================================================================
            if needs_admin and not state.get("error"):
                yield {"stage": "Analyzing your request..."}
                yield {
                    "agent_event": {
                        "agent": "admin",
                        "status": "started",
                        "description": "Analyzing admin operation request",
                    }
                }

                admin_start = time.time()
                admin_result = await admin_node(state)
                admin_duration = int((time.time() - admin_start) * 1000)

                state = {**state, **admin_result}

                yield {
                    "agent_event": {
                        "agent": "admin",
                        "status": "completed",
                        "duration_ms": admin_duration,
                        "result": {
                            "operation": state.get("admin_result", {}).get("operation"),
                            "status": (
                                "needs_info"
                                if state.get("admin_result", {}).get("needs_info")
                                else "pending"
                                if state.get("admin_result", {}).get("pending")
                                else "ready"
                            ),
                        },
                    }
                }

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

                # Otherwise, generate a response with synthesis
                yield {"stage": "Generating response..."}
                yield {
                    "agent_event": {
                        "agent": "synthesis",
                        "status": "started",
                        "description": "Generating response for admin result",
                    }
                }

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
                    text = extract_text_from_chunk(chunk)
                    if text:
                        yield text

                yield {
                    "agent_event": {
                        "agent": "synthesis",
                        "status": "completed",
                    }
                }
                yield {"citations": []}
                return

            # ================================================================
            # Step 2: Kafka context (if needed)
            # ================================================================
            if needs_cluster and not state.get("error"):
                yield {"stage": "Fetching cluster info..."}
                yield {
                    "agent_event": {
                        "agent": "kafka",
                        "status": "started",
                        "description": "Retrieving cluster metadata",
                    }
                }

                kafka_start = time.time()
                kafka_result = await kafka_node(state)
                kafka_duration = int((time.time() - kafka_start) * 1000)

                state = {**state, **kafka_result}

                cluster_ctx = state.get("cluster_context", {})
                yield {
                    "agent_event": {
                        "agent": "kafka",
                        "status": "completed",
                        "duration_ms": kafka_duration,
                        "result": {
                            "broker_count": cluster_ctx.get("broker_count", 0),
                            "topic_count": cluster_ctx.get("topic_count", 0),
                        },
                    }
                }

                # Send cluster context to frontend
                if cluster_ctx:
                    yield {"cluster_context": cluster_ctx}

            # ================================================================
            # Step 3: Retrieval (only if needed!)
            # ================================================================
            if needs_retrieval and not state.get("error"):
                yield {"stage": "Searching documentation..."}
                yield {
                    "agent_event": {
                        "agent": "retrieval",
                        "status": "started",
                        "description": "Searching vector store for relevant documents",
                    }
                }

                retrieval_start = time.time()
                retrieval_result = await retrieval_node(state)
                retrieval_duration = int((time.time() - retrieval_start) * 1000)

                state = {**state, **retrieval_result}

                # Build retrieval results for frontend visibility
                docs = state.get("retrieved_docs", [])
                retrieval_items = []
                reranked = False
                reranking_model = None

                for doc in docs[:10]:  # Limit to 10 for display
                    metadata = doc.metadata or {}
                    rerank_score = metadata.get("rerank_score")
                    if rerank_score is not None:
                        reranked = True
                        reranking_model = metadata.get("reranking_model")

                    retrieval_items.append(
                        {
                            "source": metadata.get("source", ""),
                            "source_name": metadata.get("source_name", "Unknown"),
                            "content_preview": doc.page_content[:200] + "..."
                            if len(doc.page_content) > 200
                            else doc.page_content,
                            "similarity_score": metadata.get("relevance_score", 0),
                            "rerank_score": rerank_score,
                            "collection": metadata.get("collection", ""),
                            "search_query": metadata.get("search_query", ""),
                        }
                    )

                yield {
                    "retrieval_results": {
                        "docs": retrieval_items,
                        "total": len(docs),
                        "queries_expanded": len(state.get("sub_goals", [])) + 1,
                        "reranked": reranked,
                        "reranking_model": reranking_model,
                    }
                }

                yield {
                    "agent_event": {
                        "agent": "retrieval",
                        "status": "completed",
                        "duration_ms": retrieval_duration,
                        "result": {
                            "docs_found": len(docs),
                            "reranked": reranked,
                        },
                    }
                }

                # ============================================================
                # Step 4: Validation (only if we retrieved docs)
                # ============================================================
                if docs:
                    yield {"stage": "Validating sources..."}
                    yield {
                        "agent_event": {
                            "agent": "validation",
                            "status": "started",
                            "description": "Filtering and validating document relevance",
                        }
                    }

                    validation_start = time.time()
                    validation_result = await validation_node(state)
                    validation_duration = int((time.time() - validation_start) * 1000)

                    state = {**state, **validation_result}

                    validated_docs = state.get("validated_docs", [])
                    filtered_count = len(docs) - len(validated_docs)

                    yield {
                        "validation_results": {
                            "validated": len(validated_docs),
                            "filtered": filtered_count,
                            "results": [],  # Simplified - could add per-doc validation results
                        }
                    }

                    yield {
                        "agent_event": {
                            "agent": "validation",
                            "status": "completed",
                            "duration_ms": validation_duration,
                            "result": {
                                "validated": len(validated_docs),
                                "filtered": filtered_count,
                            },
                        }
                    }

            # ================================================================
            # Step 5: Streaming synthesis
            # ================================================================
            yield {"stage": "Generating response..."}
            yield {
                "agent_event": {
                    "agent": "synthesis",
                    "status": "started",
                    "description": "Generating final response",
                }
            }

            synthesis_start = time.time()
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
                text = extract_text_from_chunk(chunk)
                if text:
                    yield text

            synthesis_duration = int((time.time() - synthesis_start) * 1000)
            yield {
                "agent_event": {
                    "agent": "synthesis",
                    "status": "completed",
                    "duration_ms": synthesis_duration,
                }
            }

            # Yield final citations (only if we have docs)
            citations = extract_citations(docs) if docs else []
            yield {"citations": citations}

        except Exception as e:
            error_msg = str(e) if e else "Unknown error"
            logger.error(f"Streaming error: {error_msg}")
            yield {
                "agent_event": {
                    "agent": "error",
                    "status": "error",
                    "result": {"error": error_msg},
                }
            }
            yield f"Error: {error_msg}"


# Singleton orchestrator
_orchestrator: AgentOrchestrator | None = None


def get_orchestrator() -> AgentOrchestrator:
    """Get the singleton orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator
