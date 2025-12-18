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
2. **admin**: The user wants to interact with their connected cluster - ANY cluster operation including:
   - READ operations: list topics, describe topic, describe cluster, list consumer groups, get offsets
   - WRITE operations: create topic, delete topic, alter config, add partitions, delete consumer group
3. **both**: The question needs BOTH documentation AND cluster context (e.g., "Is my topic X configured correctly?", "Am I following best practices?").
4. **direct**: Simple greetings.
5. **help**: The user is asking what you can do, what operations are available, or asking for help.

### Admin Route (route = "admin") - USE FOR ALL CLUSTER OPERATIONS:
Use this route when the user wants to:
- **List/show cluster resources**: "list topics", "show me my topics", "what topics exist", "list consumer groups"
- **Describe/inspect resources**: "describe topic X", "show topic config", "what are the partitions for topic Y"
- **Get cluster info**: "show cluster status", "describe the cluster", "how many brokers"
- **Create resources**: "create a topic called events", "make a new topic"
- **Modify resources**: "add partitions", "change retention", "alter topic config"
- **Delete resources**: "delete topic", "remove consumer group"

### Help Route (route = "help"):
Use this when the user asks:
- "What can you do?"
- "What operations are available?"
- "Help" or "How do I use this?"

### Web Search:
Set needs_web_search=true for knowledge/documentation questions where current info helps.
Set needs_web_search=false for:
- Cluster operations (admin route)
- Simple greetings or help

### Response Format:
Respond with ONLY a valid JSON object. Fields:
- "route": One of "retrieval", "admin", "both", "direct", or "help"
- "sub_goals": List of 1-3 specific sub-questions (empty for "direct" or "help")
- "needs_web_search": Boolean
- "reasoning": Brief explanation

Examples:
{{"route": "retrieval", "sub_goals": ["Kafka producer configuration"], "needs_web_search": true, "reasoning": "Docs question"}}
{{"route": "admin", "sub_goals": ["List all topics"], "needs_web_search": false, "reasoning": "User wants to see their cluster topics"}}
{{"route": "admin", "sub_goals": ["Describe topic orders"], "needs_web_search": false, "reasoning": "User wants topic details"}}
{{"route": "admin", "sub_goals": ["Create topic events"], "needs_web_search": false, "reasoning": "User wants to create a topic"}}"""


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
        needs_cluster = route == "both"  # Only "both" needs kafka context alongside docs
        needs_retrieval = route in ["retrieval", "both"]
        needs_admin = route == "admin"
        needs_web_search = result.get("needs_web_search", False) and web_search_available

        # If no cluster connected but admin route requested, show error
        if needs_admin and not has_cluster:
            logger.warning("Admin route requested but no cluster connected")
            return {
                "route": "direct",
                "sub_goals": [],
                "needs_cluster_context": False,
                "needs_retrieval": False,
                "needs_web_search": False,
                "needs_admin_operation": False,
                "error": "No Kafka cluster connected. Please connect to a cluster in the Cluster page first.",
            }

        # If "both" route but no cluster, fall back to retrieval only
        if route == "both" and not has_cluster:
            logger.warning("Both route requested but no cluster connected, using retrieval only")
            needs_cluster = False
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
        return "synthesis"

    route = state.get("route", "retrieval")

    # Direct responses (greetings) go straight to synthesis
    if route == "direct":
        return "synthesis"

    # Help/capability questions go to the help node
    if route == "help":
        return "help"

    if state.get("needs_admin_operation"):
        return "admin"

    # "both" route - get cluster context first, then retrieval
    if state.get("needs_cluster_context"):
        return "kafka"

    return "retrieval"
