"""Router agent for decomposing questions and routing to appropriate agents."""

import json
import re

from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from kgpt.agents.state import AgentState
from kgpt.llm import get_llm

ROUTER_SYSTEM_PROMPT = """You are a senior technical router for a Kafka/Confluent expert system.
Your job is to analyze the user's question and route to the correct agents.

### Routing Logic:
1. **retrieval**: The question is about Kafka concepts, documentation, "how-to" guides, or general knowledge.
2. **kafka**: The question is about the *current state* of the user's connected cluster (topics, configs, lag).
3. **both**: The question compares documentation best practices with the actual cluster state (e.g., "Is my topic X configured correctly?").
4. **direct**: Simple greetings or questions that don't need any lookup.

### Response Format:
Respond with ONLY a valid JSON object, no other text. Fields:
- "route": One of "retrieval", "kafka", "both", or "direct"
- "sub_goals": List of 1-3 specific sub-questions (empty list for "direct")
- "reasoning": Brief explanation of your routing choice

Example:
{{"route": "retrieval", "sub_goals": ["Kafka producer configuration options"], "reasoning": "Documentation lookup needed"}}"""


ROUTER_USER_PROMPT = """Question: {question}
Has cluster connection: {has_cluster}

Analyze the question and provide your routing decision:"""


def extract_json(text: str) -> dict:
    """Extract JSON from text that may contain additional content."""
    # Try to parse directly first
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in the text
    json_match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    # Try to find JSON with nested objects
    json_match = re.search(r"\{.*\}", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not extract valid JSON from: {text[:200]}")


def create_router_agent():
    """Create the router agent chain."""
    llm = get_llm(temperature=0)  # Router should be deterministic

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", ROUTER_SYSTEM_PROMPT),
            ("human", ROUTER_USER_PROMPT),
        ]
    )

    chain = prompt | llm
    return chain


async def router_node(state: AgentState) -> dict:
    """
    Router node that analyzes the question and decides routing.

    Returns updated state with sub_goals and routing decision.
    """
    logger.info(f"Router analyzing question: {state['question'][:100]}...")

    try:
        chain = create_router_agent()

        # Check if we have a cluster connection (check global context, not state)
        from kgpt.agents.kafka_agent import get_cluster_context

        cluster_context = get_cluster_context()
        has_cluster = cluster_context is not None

        logger.info(f"Router: has_cluster={has_cluster}")

        response = await chain.ainvoke(
            {
                "question": state["question"],
                "has_cluster": "Yes" if has_cluster else "No",
            }
        )

        # Extract JSON from the response
        result = extract_json(response.content)

        logger.info(
            f"Router decision: route={result.get('route')}, sub_goals={result.get('sub_goals')}"
        )

        return {
            "sub_goals": result.get("sub_goals", [state["question"]]),
            "needs_cluster_context": result.get("route") in ["kafka", "both"],
        }

    except Exception as e:
        logger.error(f"Router error: {e}")
        # Default to retrieval on error
        return {
            "sub_goals": [state["question"]],
            "needs_cluster_context": False,
            "error": str(e),
        }


def route_decision(state: AgentState) -> str:
    """
    Conditional edge function to determine next node based on routing.

    Returns the name of the next node to visit.
    """
    if state.get("error"):
        return "synthesis"  # Go directly to synthesis on error

    if state.get("needs_cluster_context"):
        return "kafka"
    else:
        return "retrieval"
