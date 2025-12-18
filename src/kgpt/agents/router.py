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
3. **admin**: The user wants to PERFORM an action on the cluster (create topic, delete topic, alter config, delete consumer group, add partitions).
4. **both**: The question compares documentation best practices with the actual cluster state (e.g., "Is my topic X configured correctly?").
5. **direct**: Simple greetings, or asking about capabilities/help.
6. **help**: The user is asking what you can do, what operations are available, or asking for help with capabilities.

### Admin Operations (route = "admin"):
Use this route when the user explicitly wants to:
- Delete a topic (e.g., "delete the orders topic", "remove topic X")
- Create a topic (e.g., "create a topic called events", "make a new topic")
- Describe a topic (e.g., "describe topic orders", "show me details about topic X", "what's the configuration of topic Y")
- Alter topic configuration (e.g., "change retention to 7 days for topic X", "update config for topic Y")
- Delete a consumer group (e.g., "delete consumer group my-group")
- Add partitions (e.g., "add partitions to topic X", "increase partitions to 10 for topic Y")

### Help Route (route = "help"):
Use this when the user asks:
- "What can you do?"
- "What operations are available?"
- "What admin operations can you perform?"
- "Help" or "How do I use this?"

### Response Format:
Respond with ONLY a valid JSON object, no other text. Fields:
- "route": One of "retrieval", "kafka", "admin", "both", "direct", or "help"
- "sub_goals": List of 1-3 specific sub-questions (empty list for "direct" or "help")
- "reasoning": Brief explanation of your routing choice

Example:
{{"route": "retrieval", "sub_goals": ["Kafka producer configuration options"], "reasoning": "Documentation lookup needed"}}

Example for admin:
{{"route": "admin", "sub_goals": ["Delete topic orders"], "reasoning": "User wants to delete a topic from their cluster"}}

Example for help:
{{"route": "help", "sub_goals": [], "reasoning": "User is asking about available capabilities"}}"""


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
        route = result.get("route", "retrieval")

        # Determine what we need based on route
        needs_cluster = route in ["kafka", "both", "admin"]
        needs_retrieval = route in ["retrieval", "both"]
        needs_admin = route == "admin"

        # If no cluster connected but kafka/admin route requested, fall back to retrieval
        if needs_cluster and not has_cluster:
            if route == "admin":
                logger.warning("Admin route requested but no cluster connected")
                return {
                    "route": "direct",
                    "sub_goals": [],
                    "needs_cluster_context": False,
                    "needs_retrieval": False,
                    "needs_admin_operation": False,
                    "error": "No Kafka cluster connected. Please connect to a cluster in the Cluster page before performing admin operations.",
                }
            else:
                logger.warning(
                    "Kafka route requested but no cluster connected, falling back to retrieval"
                )
                needs_cluster = False
                needs_retrieval = True
                route = "retrieval"

        logger.info(
            f"Router decision: route={route}, needs_cluster={needs_cluster}, "
            f"needs_retrieval={needs_retrieval}, needs_admin={needs_admin}, sub_goals={result.get('sub_goals')}"
        )

        return {
            "route": route,
            "sub_goals": result.get("sub_goals", [state["question"]]),
            "needs_cluster_context": needs_cluster,
            "needs_retrieval": needs_retrieval,
            "needs_admin_operation": needs_admin,
        }

    except Exception as e:
        logger.error(f"Router error: {e}")
        # Default to retrieval on error
        return {
            "route": "retrieval",
            "sub_goals": [state["question"]],
            "needs_cluster_context": False,
            "needs_retrieval": True,
            "error": str(e),
        }


def route_decision(state: AgentState) -> str:
    """
    Conditional edge function to determine next node based on routing.

    Returns the name of the next node to visit.
    """
    if state.get("error"):
        return "synthesis"  # Go directly to synthesis on error

    route = state.get("route", "retrieval")

    # Direct route or help - skip everything, go straight to synthesis
    if route in ["direct", "help"]:
        return "synthesis"

    # Admin route - go to admin node
    if state.get("needs_admin_operation"):
        return "admin"

    # Kafka-only or both - start with kafka
    if state.get("needs_cluster_context"):
        return "kafka"

    # Retrieval-only
    return "retrieval"
