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

    if "brokers" in context:
        sections.append(f"- Brokers: {context['brokers']}")

    if "topics" in context:
        topics = context["topics"]
        if isinstance(topics, list):
            sections.append(f"- Topics ({len(topics)}): {', '.join(topics[:10])}")
            if len(topics) > 10:
                sections.append(f"  ... and {len(topics) - 10} more")

    if "topic_configs" in context:
        sections.append(f"- Topic Configuration: {context['topic_configs']}")

    if "consumer_groups" in context:
        sections.append(f"- Consumer Groups: {context['consumer_groups']}")

    if "cluster_id" in context:
        sections.append(f"- Cluster ID: {context['cluster_id']}")

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
