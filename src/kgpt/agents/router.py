"""Router agent for decomposing questions and routing to appropriate agents."""

import json
import re

from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from kgpt.agents.state import AgentState
from kgpt.agents.web_search import is_web_search_enabled
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

### Web Search (IMPORTANT - be proactive):
Set needs_web_search=true for MOST knowledge questions. Only skip web search for:
- Simple greetings or help requests
- Questions about the user's OWN cluster state
- Admin operations on the user's cluster
- Very basic/fundamental concepts that don't change (e.g., "what is a topic?")

Otherwise, DEFAULT to needs_web_search=true when:
- ANY question about Kafka features, capabilities, or how things work
- Questions about best practices, recommendations, or "how should I..."
- Questions about troubleshooting, debugging, or error messages
- Questions comparing approaches or asking "which is better"
- Questions about performance, tuning, or optimization
- Questions about specific versions, features, or releases
- Questions about integrations with other tools
- Any question where current/complete information would help

The web provides up-to-date information that complements our documentation.
When in doubt, search the web - it's better to have more context than less.

### Response Format:
Respond with ONLY a valid JSON object, no other text. Fields:
- "route": One of "retrieval", "kafka", "admin", "both", "direct", or "help"
- "sub_goals": List of 1-3 specific sub-questions (empty list for "direct" or "help")
- "needs_web_search": Boolean - whether to search the web for current info
- "reasoning": Brief explanation of your routing choice

Example:
{{"route": "retrieval", "sub_goals": ["Kafka producer configuration options"], "needs_web_search": true, "reasoning": "Documentation + web for current best practices"}}

Example for simple greeting:
{{"route": "direct", "sub_goals": [], "needs_web_search": false, "reasoning": "Simple greeting, no search needed"}}

Example for admin:
{{"route": "admin", "sub_goals": ["Delete topic orders"], "needs_web_search": false, "reasoning": "User wants to delete a topic from their cluster"}}"""


ROUTER_USER_PROMPT = """Question: {question}
Has cluster connection: {has_cluster}
Web search available: {web_search_available}

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
    llm = get_llm(temperature=0, streaming=False)  # Router should be deterministic

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

        # Check if we have a cluster connection
        from kgpt.agents.kafka_agent import get_cluster_context

        cluster_context = get_cluster_context()
        has_cluster = cluster_context is not None

        # Check if web search is available
        web_search_available = is_web_search_enabled()

        logger.debug(f"Router: has_cluster={has_cluster}, web_search={web_search_available}")

        response = await chain.ainvoke(
            {
                "question": state["question"],
                "has_cluster": "Yes" if has_cluster else "No",
                "web_search_available": "Yes" if web_search_available else "No",
            }
        )

        # Extract JSON from the response
        result = extract_json(response.content)
        route = result.get("route", "retrieval")

        # Determine what we need based on route
        needs_cluster = route in ["kafka", "both", "admin"]
        needs_retrieval = route in ["retrieval", "both"]
        needs_admin = route == "admin"
        needs_web_search = result.get("needs_web_search", False) and web_search_available

        # If no cluster connected but kafka/admin route requested, fall back to retrieval
        if needs_cluster and not has_cluster:
            if route == "admin":
                logger.warning("Admin route requested but no cluster connected")
                return {
                    "route": "direct",
                    "sub_goals": [],
                    "needs_cluster_context": False,
                    "needs_retrieval": False,
                    "needs_web_search": False,
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

        reasoning = result.get("reasoning", "")
        logger.info(
            f"Router decision: route={route}, cluster={needs_cluster}, "
            f"retrieval={needs_retrieval}, web_search={needs_web_search}, "
            f"admin={needs_admin}"
        )

        return {
            "route": route,
            "sub_goals": result.get("sub_goals", [state["question"]]),
            "reasoning": reasoning,
            "needs_cluster_context": needs_cluster,
            "needs_retrieval": needs_retrieval,
            "needs_web_search": needs_web_search,
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
            "needs_web_search": False,
            "needs_admin_operation": False,
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
