"""Streaming query execution with agent activity visibility and parallel execution."""

import asyncio
import time
from collections.abc import AsyncGenerator

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from kgpt.agents.admin import admin_node
from kgpt.agents.kafka_agent import kafka_node
from kgpt.agents.query_enhancer import get_web_search_query
from kgpt.agents.retrieval import extract_doc_citations, retrieval_node
from kgpt.agents.router import router_node
from kgpt.agents.state import AgentState
from kgpt.agents.synthesis import (
    ADMIN_SYNTHESIS_SYSTEM_PROMPT,
    ADMIN_SYNTHESIS_USER_PROMPT,
    SYNTHESIS_SYSTEM_PROMPT,
    SYNTHESIS_USER_PROMPT,
    format_admin_result,
    format_cluster_context,
    format_documents,
)
from kgpt.agents.web_search import (
    extract_web_citations,
    format_web_results_for_context,
    web_search,
)
from kgpt.llm import get_llm

from .responses import get_help_response
from .text_utils import extract_text_from_chunk


async def query_stream_with_stages(
    question: str,
    chat_history: list | None = None,
    compiled_graph=None,
) -> AsyncGenerator[str | dict, None]:
    """
    Process a question with streaming output, stage updates, and agent activity events.

    Features:
    - Parallel execution of retrieval, web search, and cluster context
    - Web search via Exa for real-time information
    - No per-document validation (relies on reranking)
    - Inline citations in responses

    Yields:
        - {"stage": "..."} for thinking stage updates
        - {"agent_event": {...}} for agent activity (start/complete/error)
        - {"routing_decision": {...}} for routing info
        - {"retrieval_results": {...}} for retrieved docs
        - {"web_results": {...}} for web search results
        - {"cluster_context": {...}} for cluster info
        - {"admin_result": {...}} for admin operation result
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
        "needs_retrieval": True,
        "needs_web_search": False,
        "needs_admin_operation": False,
        "route": "retrieval",
        "admin_operation": None,
        "retrieved_docs": [],
        "web_results": [],
        "cluster_context": None,
        "admin_result": None,
        "answer": "",
        "citations": [],
        "messages": messages,
        "error": None,
    }

    try:
        # Step 1: Router (single LLM call)
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
        needs_web = state.get("needs_web_search", False)
        needs_admin = state.get("needs_admin_operation", False)
        sub_goals = state.get("sub_goals", [])
        reasoning = state.get("reasoning", "")

        # Emit routing decision
        yield {
            "routing_decision": {
                "route": route,
                "reasoning": reasoning,
                "sub_goals": sub_goals,
                "needs_cluster": needs_cluster,
                "needs_retrieval": needs_retrieval,
                "needs_web_search": needs_web,
                "needs_admin": needs_admin,
            }
        }

        yield {
            "agent_event": {
                "agent": "router",
                "status": "completed",
                "duration_ms": router_duration,
                "result": {
                    "route": route,
                    "sub_goals": sub_goals,
                    "needs_web_search": needs_web,
                },
            }
        }

        logger.info(
            f"Route: {route}, cluster={needs_cluster}, retrieval={needs_retrieval}, "
            f"web={needs_web}, admin={needs_admin}"
        )

        # Handle help route
        if route == "help":
            yield {"stage": ""}
            yield {
                "agent_event": {
                    "agent": "synthesis",
                    "status": "started",
                    "description": "Generating help response",
                }
            }

            help_response = get_help_response()
            for char in help_response:
                yield char

            yield {"agent_event": {"agent": "synthesis", "status": "completed"}}
            yield {"citations": [], "done": True}
            return

        # Handle admin operations
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

            # For structured UI cards, don't generate text
            if needs_info or is_unclear or is_pending:
                yield {"stage": ""}
                yield {"citations": [], "done": True}
                return

            # For errors, return
            if has_error:
                yield {"stage": ""}
                yield {"citations": [], "done": True}
                return

            # Generate response with synthesis
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

            yield {"agent_event": {"agent": "synthesis", "status": "completed"}}
            yield {"citations": [], "done": True}
            return

        # Step 2: Parallel execution of retrieval, web search, and cluster context
        yield {"stage": "Gathering information..."}

        parallel_tasks = []
        task_names = []

        # Start parallel tasks
        if needs_cluster and not state.get("error"):
            yield {
                "agent_event": {
                    "agent": "kafka",
                    "status": "started",
                    "description": "Retrieving cluster metadata",
                }
            }
            parallel_tasks.append(kafka_node(state))
            task_names.append("kafka")

        if needs_retrieval and not state.get("error"):
            yield {
                "agent_event": {
                    "agent": "retrieval",
                    "status": "started",
                    "description": "Searching documentation",
                }
            }
            parallel_tasks.append(retrieval_node(state))
            task_names.append("retrieval")

        if needs_web and not state.get("error"):
            # Enhance query with Kafka domain context for better web results
            enhanced_query = get_web_search_query(
                state["question"],
                sub_goals=state.get("sub_goals"),
            )
            yield {
                "agent_event": {
                    "agent": "web_search",
                    "status": "started",
                    "description": f"Searching: {enhanced_query[:50]}...",
                }
            }
            parallel_tasks.append(web_search(enhanced_query))
            task_names.append("web_search")

        # Execute in parallel
        parallel_start = time.time()
        if parallel_tasks:
            results = await asyncio.gather(*parallel_tasks, return_exceptions=True)
        else:
            results = []
        parallel_duration = int((time.time() - parallel_start) * 1000)

        # Process results
        for i, (task_name, result) in enumerate(zip(task_names, results)):
            if isinstance(result, Exception):
                logger.error(f"{task_name} failed: {result}")
                yield {
                    "agent_event": {
                        "agent": task_name,
                        "status": "error",
                        "result": {"error": str(result)},
                    }
                }
                continue

            if task_name == "kafka":
                state = {**state, **result}
                cluster_ctx = state.get("cluster_context", {})
                yield {
                    "agent_event": {
                        "agent": "kafka",
                        "status": "completed",
                        "duration_ms": parallel_duration,
                        "result": {
                            "broker_count": cluster_ctx.get("broker_count", 0),
                            "topic_count": cluster_ctx.get("topic_count", 0),
                        },
                    }
                }
                if cluster_ctx:
                    yield {"cluster_context": cluster_ctx}

            elif task_name == "retrieval":
                state = {**state, **result}
                docs = state.get("retrieved_docs", [])
                retrieval_items = []
                reranked = False
                reranking_model = None

                for doc in docs[:10]:
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
                        }
                    )

                yield {
                    "retrieval_results": {
                        "docs": retrieval_items,
                        "total": len(docs),
                        "queries_used": len(state.get("sub_goals", [])) + 1,
                        "reranked": reranked,
                        "reranking_model": reranking_model,
                    }
                }

                yield {
                    "agent_event": {
                        "agent": "retrieval",
                        "status": "completed",
                        "duration_ms": parallel_duration,
                        "result": {"docs_found": len(docs), "reranked": reranked},
                    }
                }

            elif task_name == "web_search":
                # web_search returns list directly, not a dict
                web_results = result if isinstance(result, list) else []
                state["web_results"] = web_results

                if not web_results:
                    logger.warning(
                        "Web search returned no results - check API key configuration and query"
                    )

                yield {
                    "web_results": {
                        "results": [
                            {
                                "title": r.get("title", ""),
                                "url": r.get("url", ""),
                                "highlights": r.get("highlights", []),
                            }
                            for r in web_results[:5]
                        ],
                        "total": len(web_results),
                    }
                }

                yield {
                    "agent_event": {
                        "agent": "web_search",
                        "status": "completed",
                        "duration_ms": parallel_duration,
                        "result": {"results_found": len(web_results)},
                    }
                }

        # Step 3: Streaming synthesis (single LLM call)
        yield {"stage": "Generating response..."}
        yield {
            "agent_event": {
                "agent": "synthesis",
                "status": "started",
                "description": "Generating final response",
            }
        }

        synthesis_start = time.time()
        docs = state.get("retrieved_docs", [])
        web_results = state.get("web_results", [])

        # Format context for synthesis
        documents_text = format_documents(docs)
        web_section = format_web_results_for_context(web_results)
        cluster_section = format_cluster_context(state.get("cluster_context"))

        # Combine all context
        full_context = documents_text
        if web_section:
            full_context = f"{documents_text}\n\n{web_section}"

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
                "documents": full_context,
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
                "result": {"docs_used": len(docs), "web_results_used": len(web_results)},
            }
        }

        # Combine citations from docs and web
        doc_citations = extract_doc_citations(docs) if docs else []
        web_citations = extract_web_citations(web_results) if web_results else []
        all_citations = doc_citations + web_citations

        yield {"citations": all_citations, "done": True}

    except Exception as e:
        error_msg = str(e) if e else "Unknown error"
        logger.error(f"Streaming error: {error_msg}", exc_info=True)
        yield {
            "agent_event": {
                "agent": "error",
                "status": "error",
                "result": {"error": error_msg},
            }
        }
        yield f"Error: {error_msg}"
        yield {"citations": [], "done": True}
