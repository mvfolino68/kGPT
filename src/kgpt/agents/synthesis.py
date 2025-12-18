"""Synthesis agent for generating the final answer."""

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from kgpt.agents.state import AgentState
from kgpt.llm import get_llm

SYNTHESIS_SYSTEM_PROMPT = """You are a Kafka expert assistant. Be direct, concise, and helpful.

### Rules:
1. **Answer directly** - Get to the point. Don't add unnecessary preamble or headers like "Analysis:" or "Answer:".
2. **Be concise** - Users want quick, actionable answers. Avoid verbose explanations unless asked.
3. **Use context** - If cluster info is provided, use it to give specific answers about their cluster.
4. **Only recommend when asked** - Don't add unsolicited recommendations, best practices, or suggestions.
5. **Format cleanly** - Use Markdown for code blocks and lists. Keep formatting minimal and readable.

### What NOT to do:
- Don't start with "Based on the context..." or similar phrases
- Don't add sections like "Recommendations:", "Best Practices:", "Additional Tips:" unless specifically asked
- Don't repeat the question back
- Don't add disclaimers or caveats unless critical
- Don't say "Sources:" at the end - citations are handled separately"""


SYNTHESIS_USER_PROMPT = """Question: {question}

{cluster_section}

{documents}

Provide a direct, helpful answer:"""


# Admin operation-specific prompts for GATHERING INFO (asking questions)
ADMIN_GATHERING_SYSTEM_PROMPT = """You are a friendly Kafka admin assistant helping the user set up an operation.
You need to gather some information before proceeding.

### Rules:
1. **Be conversational** - Ask questions naturally, not like a form
2. **Explain briefly** - Help them understand what each parameter means if it's not obvious
3. **Provide examples** - Give example values when helpful
4. **Show defaults** - Mention default values so they know what to expect
5. **Be encouraging** - This should feel like a helpful conversation, not an interrogation

### Format:
- Acknowledge what they want to do
- Ask the questions in a natural way
- For each question, briefly explain why it matters or give examples
- Don't number questions like a form - weave them into conversation"""


ADMIN_GATHERING_USER_PROMPT = """User's request: {question}

Analysis of what's needed:
{admin_result}

Cluster context:
{cluster_section}

Have a helpful conversation to gather the missing information:"""


# Admin operation-specific prompts for PENDING operations (confirmation required)
ADMIN_PENDING_SYSTEM_PROMPT = """You are a Kafka admin assistant. The user has requested an admin operation.
Present the operation details clearly so they can review and confirm before execution.

### Rules:
1. **Summarize the operation** - Clearly state what will happen if they confirm
2. **Show key parameters** - Include topic names, partition counts, config values, etc.
3. **Note any risks** - For destructive operations, briefly mention what could be affected
4. **Be concise** - Don't over-explain, just present the facts
5. **Use structured format** - Make it easy to scan with bullet points or a table

### Format:
- Start with a brief summary of the operation
- List the key parameters
- If destructive (delete), add a brief warning
- End by noting they can confirm or cancel"""


ADMIN_PENDING_USER_PROMPT = """Original request: {question}

{admin_result}

{cluster_section}

Present this pending operation for user confirmation:"""


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
    """Format documents for the synthesis prompt."""
    if not docs:
        return "No documents found."

    formatted = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "Unknown source")
        source_name = doc.metadata.get("source_name", "")

        formatted.append(f"""
--- Document {i} ---
Source: {source_name} - {source}
Content:
{doc.page_content[:3000]}
""")

    return "\n".join(formatted)


def format_cluster_context(context: dict | None) -> str:
    """Format cluster context for the prompt."""
    if not context:
        return ""

    sections = ["Kafka Cluster Context:"]

    # Use broker_count if available, otherwise count broker entries
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
            # Format config dict nicely
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
                # Extract group IDs from list of dicts
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
                sections.append(f"  • {q}")

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


def extract_citations(docs: list[Document]) -> list[str]:
    """Extract source citations from documents."""
    citations = []
    seen = set()

    for doc in docs:
        source = doc.metadata.get("source", "")
        source_name = doc.metadata.get("source_name", "")

        if source and source not in seen:
            seen.add(source)
            if source.startswith("http"):
                citations.append(source)
            elif source_name:
                citations.append(f"{source_name}: {source}")
            else:
                citations.append(source)

    return citations


async def synthesis_node(state: AgentState) -> dict:
    """
    Synthesis node that generates the final answer.

    Combines validated documents and cluster context to produce a comprehensive answer.
    """
    logger.info("Synthesis agent generating answer...")

    # Handle error state
    if state.get("error") and not state.get("validated_docs"):
        return {
            "answer": f"I encountered an error while processing your question: {state['error']}. Please try again.",
            "citations": [],
        }

    # Get documents (prefer validated, fall back to retrieved)
    docs = state.get("validated_docs", []) or state.get("retrieved_docs", [])

    # Format inputs
    documents_text = format_documents(docs)
    cluster_section = format_cluster_context(state.get("cluster_context"))

    # Create synthesis chain
    llm = get_llm(streaming=True)
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
        citations = extract_citations(docs)

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


async def synthesis_node_streaming(state: AgentState):
    """
    Streaming version of synthesis node.

    Yields tokens as they are generated for real-time display.
    """
    logger.info("Synthesis agent generating answer (streaming)...")

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

    full_response = ""
    async for chunk in chain.astream(
        {
            "question": state["question"],
            "cluster_section": cluster_section,
            "documents": documents_text,
        }
    ):
        if hasattr(chunk, "content"):
            full_response += chunk.content
            yield chunk.content

    # Final state update
    citations = extract_citations(docs)
    yield {"answer": full_response, "citations": citations}
