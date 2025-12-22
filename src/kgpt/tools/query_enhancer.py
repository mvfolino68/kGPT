"""
Query Enhancement Tool.

This tool uses an LLM to enhance user queries with Kafka-specific domain context to improve search relevance.
It handles disambiguation (e.g., "kraft" -> "KRaft") and context injection intelligently.
"""

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from loguru import logger
from pydantic import BaseModel, Field

from kgpt.llm import get_llm

SYSTEM_PROMPT = """You are an expert search query optimizer for Apache Kafka and Confluent.
Your goal is to rewrite user queries to maximize search relevance in technical documentation.

Rules:
1. Disambiguate terms (e.g., "kraft" -> "KRaft Consensus", "isr" -> "In-Sync Replicas").
2. Add context (e.g., append "Apache Kafka" if the query is generic like "partition assignment").
3. Fix technical typos.
4. Return ONLY the rewritten query text. No quotes, no explanations.
"""


class QueryEnhancerInput(BaseModel):
    """Input for the query enhancer tool."""

    query: str = Field(description="The search query to enhance")
    add_domain_suffix: bool = Field(
        default=True,
        description="Whether to append 'Apache Kafka' if context is missing (handled by LLM now)",
    )


async def enhance_query_for_web_search(
    query: str, sub_goals: list[str] | None = None, add_domain_suffix: bool = True
) -> str:
    """
    Enhance a query using the LLM.
    This function is async because it calls the LLM.
    """
    return await _enhance_query_logic(query, add_domain_suffix)


async def _enhance_query_logic(query: str, add_domain_suffix: bool) -> str:
    """Internal LLM enhancement logic."""
    try:
        llm = get_llm()
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Rewrite this query: {query}"),
        ]

        response = await llm.ainvoke(messages)
        enhanced = response.content.strip().strip('"')

        if enhanced != query:
            logger.info(f"Enhanced query (LLM): '{query}' -> '{enhanced}'")

        return enhanced

    except Exception as e:
        logger.error(f"Query enhancement failed: {e}")
        return query  # Fallback to original


@tool("enhance_query", args_schema=QueryEnhancerInput)
async def query_enhancer_tool(query: str, add_domain_suffix: bool = True) -> str:
    """
    Enhance a search query by adding Kafka domain context and disambiguating terms.
    Use this before performing searches to ensure relevance.
    Example: "kraft issues" -> "KRaft Apache Kafka issues"
    """
    return await _enhance_query_logic(query, add_domain_suffix)
