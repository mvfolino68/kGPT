"""Streaming query execution with agent activity visibility and parallel execution."""

import asyncio
import time
from collections.abc import AsyncGenerator

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from kgpt.agents.admin_node import admin_node
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


def _format_executed_result(admin_res: dict) -> str:
    """Format an executed admin operation result for synthesis."""
    lines = ["Admin Operation Result:"]
    lines.append(
        f"- Operation: {admin_res.get('operation_name', admin_res.get('operation', 'Unknown'))}"
    )
    lines.append(f"- Status: {'SUCCESS' if admin_res.get('success') else 'FAILED'}")

    if admin_res.get("message"):
        lines.append(f"- Message: {admin_res['message']}")

    data = admin_res.get("data", {})

    # Format data based on operation type
    operation = admin_res.get("operation", "")

    if operation == "list_topics":
        topics = data.get("topics", [])
        lines.append(f"- Total topics: {len(topics)}")
        if topics:
            lines.append("- Topics:")
            for t in topics[:20]:
                if isinstance(t, dict):
                    lines.append(
                        f"  - {t.get('name', '?')} ({t.get('partitions', '?')} partitions)"
                    )
                else:
                    lines.append(f"  - {t}")
            if len(topics) > 20:
                lines.append(f"  ... and {len(topics) - 20} more")

    elif operation == "describe_topic":
        lines.append(f"- Topic: {data.get('topic', '?')}")
        lines.append(f"- Partitions: {data.get('partition_count', '?')}")
        lines.append(f"- Replication Factor: {data.get('replication_factor', '?')}")

        partitions = data.get("partitions", [])
        if partitions:
            lines.append("- Partition Details:")
            for p in partitions[:5]:
                lines.append(
                    f"  - Partition {p.get('partition', '?')}: "
                    f"leader={p.get('leader', '?')}, "
                    f"replicas={p.get('replicas', [])}, "
                    f"ISRs={p.get('isrs', [])}"
                )
            if len(partitions) > 5:
                lines.append(f"  ... and {len(partitions) - 5} more partitions")

        config = data.get("configuration", {})
        if config:
            lines.append("- Key Configuration:")
            for k, v in list(config.items())[:10]:
                lines.append(f"  - {k}: {v}")

    elif operation == "list_consumer_groups":
        groups = data.get("groups", [])
        lines.append(f"- Total groups: {len(groups)}")
        if groups:
            lines.append("- Groups:")
            for g in groups[:20]:
                if isinstance(g, dict):
                    lines.append(f"  - {g.get('group_id', '?')} (state: {g.get('state', '?')})")
                else:
                    lines.append(f"  - {g}")
            if len(groups) > 20:
                lines.append(f"  ... and {len(groups) - 20} more")

    elif operation == "describe_consumer_group":
        lines.append(f"- Group ID: {data.get('group_id', '?')}")
        lines.append(f"- State: {data.get('state', '?')}")
        lines.append(f"- Protocol: {data.get('protocol', '?')}")
        members = data.get("members", [])
        lines.append(f"- Members: {len(members)}")
        for m in members[:5]:
            lines.append(f"  - {m.get('client_id', '?')} @ {m.get('host', '?')}")

    elif operation == "describe_cluster":
        lines.append(f"- Cluster ID: {data.get('cluster_id', '?')}")
        lines.append(f"- Controller: Broker {data.get('controller_id', '?')}")
        lines.append(f"- Brokers: {data.get('broker_count', '?')}")
        lines.append(f"- Topics: {data.get('topic_count', '?')}")
        brokers = data.get("brokers", [])
        if brokers:
            lines.append("- Broker Details:")
            for b in brokers:
                lines.append(
                    f"  - Broker {b.get('id', '?')}: {b.get('host', '?')}:{b.get('port', '?')}"
                )

    elif operation == "get_consumer_group_offsets":
        lines.append(f"- Group ID: {data.get('group_id', '?')}")
        offsets = data.get("offsets", [])
        lines.append(f"- Offset entries: {len(offsets)}")
        for o in offsets[:10]:
            lines.append(
                f"  - {o.get('topic', '?')}[{o.get('partition', '?')}]: offset {o.get('offset', '?')}"
            )
        if len(offsets) > 10:
            lines.append(f"  ... and {len(offsets) - 10} more")

    else:
        # Generic data formatting
        for key, value in data.items():
            if isinstance(value, (list, dict)):
                lines.append(f"- {key}: {len(value) if isinstance(value, list) else 'object'}")
            else:
                lines.append(f"- {key}: {value}")

    # Include code that was executed for educational value
    if admin_res.get("code_executed"):
        lines.append("\nCode executed:")
        lines.append("```python")
        lines.append(admin_res["code_executed"])
        lines.append("```")

    return "\n".join(lines)


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
            yield {"stage": "Processing admin request..."}
            yield {
                "agent_event": {
                    "agent": "admin",
                    "status": "started",
                    "description": "Processing admin operation",
                }
            }

            admin_start = time.time()
            admin_result = await admin_node(state)
            admin_duration = int((time.time() - admin_start) * 1000)

            state = {**state, **admin_result}
            admin_res = state.get("admin_result", {})

            # Determine operation status for event
            if admin_res.get("executed"):
                op_status = "executed"
            elif admin_res.get("needs_info"):
                op_status = "needs_info"
            elif admin_res.get("pending"):
                op_status = "pending"
            elif admin_res.get("unclear"):
                op_status = "unclear"
            else:
                op_status = "error" if admin_res.get("error") else "unknown"

            yield {
                "agent_event": {
                    "agent": "admin",
                    "status": "completed",
                    "duration_ms": admin_duration,
                    "result": {
                        "operation": admin_res.get("operation"),
                        "operation_name": admin_res.get("operation_name"),
                        "status": op_status,
                    },
                }
            }

            # Send cluster context and admin result to frontend
            if state.get("cluster_context"):
                yield {"cluster_context": state["cluster_context"]}
            if admin_res:
                yield {"admin_result": admin_res}

            # Handle different admin result states
            is_executed = admin_res.get("executed", False)
            is_pending = admin_res.get("pending", False)
            needs_info = admin_res.get("needs_info", False)
            is_unclear = admin_res.get("unclear", False)
            has_error = admin_res.get("error")

            # For executed read operations, generate a natural language response
            if is_executed and admin_res.get("success"):
                yield {"stage": "Generating response..."}
                yield {
                    "agent_event": {
                        "agent": "synthesis",
                        "status": "started",
                        "description": "Generating response for executed operation",
                    }
                }

                # Format the executed operation result for synthesis
                admin_section = _format_executed_result(admin_res)
                cluster_section = format_cluster_context(state.get("cluster_context"))

                llm = get_llm(streaming=True)
                prompt = ChatPromptTemplate.from_messages(
                    [
                        ("system", ADMIN_SYNTHESIS_SYSTEM_PROMPT),
                        ("human", ADMIN_SYNTHESIS_USER_PROMPT),
                    ]
                )

                chain = prompt | llm

                content_yielded = False
                async for chunk in chain.astream(
                    {
                        "question": state["question"],
                        "admin_result": admin_section,
                        "cluster_section": cluster_section,
                    }
                ):
                    text = extract_text_from_chunk(chunk)
                    if text:
                        content_yielded = True
                        yield text

                if not content_yielded:
                    # Fallback: use the message from the result
                    yield admin_res.get("message", "Operation completed successfully.")

                yield {"agent_event": {"agent": "synthesis", "status": "completed"}}
                yield {"citations": [], "done": True}
                return

            # For pending write operations, UI handles confirmation - no text needed
            if is_pending:
                yield {"stage": ""}
                yield {"citations": [], "done": True}
                return

            # For needs_info, UI handles the input form - no text needed
            if needs_info:
                yield {"stage": ""}
                yield {"citations": [], "done": True}
                return

            # For unclear requests, UI shows operation picker - no text needed
            if is_unclear:
                yield {"stage": ""}
                yield {"citations": [], "done": True}
                return

            # For errors, show error message
            if has_error:
                yield f"Error: {has_error}"
                yield {"stage": ""}
                yield {"citations": [], "done": True}
                return

            # Fallback for any other state
            yield {"stage": ""}
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

        # Check if we have any context to work with
        has_context = bool(full_context.strip() or cluster_section.strip())
        logger.debug(
            f"Synthesis context: docs={len(docs)}, web={len(web_results)}, "
            f"cluster={bool(state.get('cluster_context'))}, has_context={has_context}"
        )

        llm = get_llm(streaming=True)
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYNTHESIS_SYSTEM_PROMPT),
                ("human", SYNTHESIS_USER_PROMPT),
            ]
        )

        chain = prompt | llm

        # Stream tokens and track if we got any content
        content_yielded = False
        chunk_count = 0
        async for chunk in chain.astream(
            {
                "question": state["question"],
                "cluster_section": cluster_section,
                "documents": full_context,
            }
        ):
            chunk_count += 1
            text = extract_text_from_chunk(chunk)
            if text:
                content_yielded = True
                yield text

        # Log warning if no content was generated
        if not content_yielded:
            logger.warning(
                f"Synthesis generated no content! Chunks received: {chunk_count}, "
                f"context available: {has_context}"
            )
            # Yield a fallback message so the user doesn't see nothing
            yield "I apologize, but I wasn't able to generate a response. Please try rephrasing your question."

        synthesis_duration = int((time.time() - synthesis_start) * 1000)
        yield {
            "agent_event": {
                "agent": "synthesis",
                "status": "completed",
                "duration_ms": synthesis_duration,
                "result": {
                    "docs_used": len(docs),
                    "web_results_used": len(web_results),
                    "content_yielded": content_yielded,
                },
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
