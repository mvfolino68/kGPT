"""Synthesis agent for generating the final answer with inline citations."""

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from kgpt.agents.state import AgentState
from kgpt.llm import get_llm

SYNTHESIS_SYSTEM_PROMPT = """You are a Kafka expert assistant. Be direct, thorough, and helpful.

### Rules:
1. **Answer directly** - Get to the point. Don't add unnecessary preamble.
2. **Be comprehensive** - Use the provided documentation to give thorough, educational answers. Include key details, architecture insights, and practical information from the sources.
3. **Use context** - If cluster info is provided, use it to give specific answers about their cluster.
4. **Cite sources** - When using information from documents or web results, cite with [1], [2], etc. matching the source numbers provided. Cite frequently when drawing from sources.
5. **Format cleanly** - Use Markdown for code blocks, lists, and headers. Structure longer answers with sections for readability.

### Response Depth:
- For conceptual questions (what is X, how does Y work): Provide detailed explanations with architecture details, key components, and how they interact
- For practical questions (how to configure X): Be specific with steps and examples
- For troubleshooting: Include common causes and solutions

### Citation Format:
- Reference sources inline like: "Kafka uses log segments for storage [1]"
- Cite when directly using information from a source
- Don't add a separate "Sources" or "References" section - citations are handled by the UI

### What NOT to do:
- Don't start with "Based on the context..." or similar phrases
- Don't repeat the question back
- Don't add disclaimers unless critical
- Don't ignore the documentation - synthesize insights from the provided sources"""


SYNTHESIS_USER_PROMPT = """Question: {question}

{cluster_section}

{documents}

Provide a direct, helpful answer with inline citations [1], [2], etc. when using source information:"""


# Admin operation-specific prompts for EXECUTED operations
ADMIN_SYNTHESIS_SYSTEM_PROMPT = """You are a Kafka admin assistant that has just executed an operation on a cluster.
Report the result clearly and concisely.

### Rules:
1. **Report the outcome** - State whether the operation succeeded or failed
2. **Be specific** - Include the operation type and affected resource (topic name, group id, etc.)
3. **On success** - Briefly confirm what was done
4. **On failure** - Explain the error clearly and suggest a fix if obvious
5. **Format cleanly** - Use Markdown for clarity

### What NOT to do:
- Don't add unnecessary warnings or caveats for successful operations
- Don't suggest additional operations unless asked
- Don't be verbose"""


ADMIN_SYNTHESIS_USER_PROMPT = """Original request: {question}

{admin_result}

{cluster_section}

Provide a clear response about the operation result:"""


def format_documents(docs: list[Document]) -> str:
    """Format documents for the synthesis prompt with numbered sources."""
    if not docs:
        return "No documentation found."

    formatted = ["Documentation Sources:"]
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "Unknown source")
        source_name = doc.metadata.get("source_name", "")

        # Derive source_name from URL if not set
        if not source_name and source:
            from urllib.parse import urlparse

            parsed = urlparse(source)
            if parsed.netloc:
                source_name = parsed.netloc
            else:
                source_name = "Documentation"
        elif not source_name:
            source_name = "Documentation"

        formatted.append(f"""
[{i}] {source_name}
URL: {source}
Content:
{doc.page_content[:2500]}
""")

    return "\n".join(formatted)


def format_cluster_context(context: dict | None) -> str:
    """Format cluster context for the prompt."""
    if not context:
        return ""

    sections = ["Kafka Cluster Context:"]

    if "broker_count" in context:
        sections.append(f"- Brokers: {context['broker_count']}")
    elif "brokers" in context:
        brokers = context["brokers"]
        if isinstance(brokers, int):
            sections.append(f"- Brokers: {brokers}")
        elif isinstance(brokers, dict):
            sections.append(f"- Brokers: {len(brokers)}")

    if "topics" in context:
        topics = context["topics"]
        if isinstance(topics, list):
            sections.append(f"- Topics ({len(topics)}): {', '.join(topics[:10])}")
            if len(topics) > 10:
                sections.append(f"  ... and {len(topics) - 10} more")

    if "topic_configs" in context:
        configs = context["topic_configs"]
        if isinstance(configs, dict):
            config_items = [f"{k}={v}" for k, v in list(configs.items())[:5]]
            sections.append(f"- Topic Configuration: {', '.join(config_items)}")
            if len(configs) > 5:
                sections.append(f"  ... and {len(configs) - 5} more settings")
        else:
            sections.append(f"- Topic Configuration: {configs}")

    if "consumer_groups" in context:
        groups = context["consumer_groups"]
        if isinstance(groups, list):
            if groups and isinstance(groups[0], dict):
                group_ids = [g.get("group_id", str(g)) for g in groups]
                sections.append(f"- Consumer Groups ({len(groups)}): {', '.join(group_ids[:10])}")
                if len(groups) > 10:
                    sections.append(f"  ... and {len(groups) - 10} more")
            else:
                sections.append(
                    f"- Consumer Groups ({len(groups)}): {', '.join(str(g) for g in groups[:10])}"
                )
        else:
            sections.append(f"- Consumer Groups: {groups}")

    if "cluster_id" in context:
        sections.append(f"- Cluster ID: {context['cluster_id']}")

    return "\n".join(sections)


def format_admin_result(result: dict | None) -> str:
    """Format admin operation result for the prompt."""
    if not result:
        return "No operation result."

    # Check if we need to gather more information
    if result.get("needs_info") or result.get("unclear"):
        sections = ["Admin Operation Analysis:"]

        if result.get("operation"):
            sections.append(f"- Detected Operation: {result['operation']}")
        else:
            sections.append("- Operation: Could not determine")

        params = result.get("params", {})
        if params:
            sections.append("- Parameters provided so far:")
            for key, value in params.items():
                sections.append(f"  - {key}: {value}")

        if result.get("missing_required"):
            sections.append(f"- Missing required info: {', '.join(result['missing_required'])}")

        if result.get("missing_optional"):
            sections.append(
                f"- Optional info not specified: {', '.join(result['missing_optional'])}"
            )

        if result.get("questions"):
            sections.append("- Questions to ask:")
            for q in result["questions"]:
                sections.append(f"  - {q}")

        return "\n".join(sections)

    # Check if this is a pending operation awaiting confirmation
    if result.get("pending"):
        sections = ["Pending Admin Operation (Awaiting Confirmation):"]
        sections.append(f"- Operation: {result.get('operation', 'unknown')}")

        params = result.get("params", {})
        if params.get("topic_name"):
            sections.append(f"- Topic: {params['topic_name']}")
        if params.get("group_id"):
            sections.append(f"- Consumer Group: {params['group_id']}")
        if params.get("num_partitions"):
            sections.append(f"- Partitions: {params['num_partitions']}")
        if params.get("replication_factor"):
            sections.append(f"- Replication Factor: {params['replication_factor']}")
        if params.get("new_total_partitions"):
            sections.append(f"- New Total Partitions: {params['new_total_partitions']}")
        if params.get("config_updates"):
            sections.append(f"- Config Updates: {params['config_updates']}")
        if params.get("config"):
            sections.append(f"- Topic Config: {params['config']}")

        if result.get("confirmation_message"):
            sections.append(f"- Impact: {result['confirmation_message']}")
        if result.get("warning_level"):
            sections.append(f"- Risk Level: {result['warning_level']}")

        return "\n".join(sections)

    # This is an executed operation result
    sections = ["Admin Operation Result:"]

    if result.get("success"):
        sections.append("- Status: SUCCESS")
        sections.append(f"- Operation: {result.get('operation', 'unknown')}")

        if result.get("topic"):
            sections.append(f"- Topic: {result['topic']}")
        if result.get("group_id"):
            sections.append(f"- Consumer Group: {result['group_id']}")
        if result.get("message"):
            sections.append(f"- Message: {result['message']}")
        if result.get("partitions"):
            sections.append(f"- Partitions: {result['partitions']}")
        if result.get("replication_factor"):
            sections.append(f"- Replication Factor: {result['replication_factor']}")
        if result.get("config_updates"):
            sections.append(f"- Config Updates: {result['config_updates']}")
    else:
        sections.append("- Status: FAILED")
        sections.append(f"- Operation: {result.get('operation', 'unknown')}")
        if result.get("error"):
            sections.append(f"- Error: {result['error']}")

    return "\n".join(sections)


async def synthesis_node(state: AgentState) -> dict:
    """
    Synthesis node that generates the final answer.

    Combines retrieved documents, web results, and cluster context to produce a comprehensive answer.
    """
    logger.info("Synthesis agent generating answer...")

    # Handle error state
    if state.get("error") and not state.get("retrieved_docs"):
        return {
            "answer": f"I encountered an error while processing your question: {state['error']}. Please try again.",
            "citations": [],
        }

    # Get documents
    docs = state.get("retrieved_docs", [])
    web_results = state.get("web_results", [])

    # Format inputs
    documents_text = format_documents(docs)

    # Add web results if available
    if web_results:
        web_section = "\n\nWeb Search Results:\n"
        start_idx = len(docs) + 1
        for i, result in enumerate(web_results, start_idx):
            web_section += f"\n[{i}] {result.get('title', 'Web Result')}\n"
            web_section += f"URL: {result.get('url', '')}\n"
            if result.get("highlights"):
                highlights = result["highlights"]
                if isinstance(highlights, list):
                    web_section += f"Key excerpts: {' ... '.join(highlights[:3])}\n"
                else:
                    web_section += f"Key excerpt: {highlights}\n"
            elif result.get("content"):
                web_section += f"Content: {result['content'][:500]}...\n"
        documents_text += web_section

    cluster_section = format_cluster_context(state.get("cluster_context"))

    # Create synthesis chain
    llm = get_llm(streaming=False)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYNTHESIS_SYSTEM_PROMPT),
            ("human", SYNTHESIS_USER_PROMPT),
        ]
    )

    chain = prompt | llm

    try:
        result = await chain.ainvoke(
            {
                "question": state["question"],
                "cluster_section": cluster_section,
                "documents": documents_text,
            }
        )

        answer = result.content

        # Build structured citations with content previews for modal display
        citations = []
        seen_urls = set()

        for doc in docs:
            source = doc.metadata.get("source", "")
            if source and source not in seen_urls:
                seen_urls.add(source)
                # Include content preview for the citation modal
                content_preview = doc.page_content[:500] if doc.page_content else ""
                citations.append(
                    {
                        "title": doc.metadata.get("source_name", "Documentation"),
                        "url": source if source.startswith("http") else "",
                        "type": "doc",
                        "content_preview": content_preview,
                    }
                )

        for result in web_results:
            url = result.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                # Include content preview from web search results
                content_preview = ""
                if result.get("highlights"):
                    highlights = result["highlights"]
                    if isinstance(highlights, list):
                        content_preview = " ... ".join(highlights[:3])
                    else:
                        content_preview = highlights
                elif result.get("content"):
                    content_preview = result["content"][:500]

                citations.append(
                    {
                        "title": result.get("title", "Web Result"),
                        "url": url,
                        "type": "web",
                        "content_preview": content_preview,
                    }
                )

        logger.info(
            f"Synthesis complete. Answer length: {len(answer)}, Citations: {len(citations)}"
        )

        return {
            "answer": answer,
            "citations": citations,
        }

    except Exception as e:
        logger.error(f"Synthesis error: {e}")
        return {
            "answer": f"I apologize, but I encountered an error generating your answer. Error: {str(e)}",
            "citations": [],
            "error": str(e),
        }
