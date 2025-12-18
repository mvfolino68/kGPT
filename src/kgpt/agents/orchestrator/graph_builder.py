"""Graph construction for the multi-agent system."""

from langgraph.graph import END, StateGraph

from kgpt.agents.admin_node import admin_node
from kgpt.agents.help_node import help_node
from kgpt.agents.kafka_agent import kafka_node
from kgpt.agents.retrieval import retrieval_node
from kgpt.agents.router import route_decision, router_node
from kgpt.agents.state import AgentState
from kgpt.agents.synthesis import synthesis_node


def create_agent_graph() -> StateGraph:
    """
    Create the multi-agent graph.

    Graph structure:
        START -> router -> [retrieval | admin | kafka | help | synthesis] -> ... -> synthesis -> END

    Routes:
    - "retrieval": docs only -> retrieval -> synthesis
    - "admin": cluster operations -> admin -> synthesis
    - "both": cluster context + docs -> kafka -> retrieval -> synthesis
    - "help": capability questions -> help -> synthesis
    - "direct": simple greetings -> synthesis
    """
    graph = StateGraph(AgentState)

    graph.add_node("router", router_node)
    graph.add_node("retrieval", retrieval_node)
    graph.add_node("kafka", kafka_node)
    graph.add_node("admin", admin_node)
    graph.add_node("help", help_node)
    graph.add_node("synthesis", synthesis_node)

    graph.set_entry_point("router")

    graph.add_conditional_edges(
        "router",
        route_decision,
        {
            "retrieval": "retrieval",
            "kafka": "kafka",  # For "both" route - get context first
            "admin": "admin",
            "help": "help",  # For capability questions
            "synthesis": "synthesis",
        },
    )

    graph.add_edge("retrieval", "synthesis")
    graph.add_edge("admin", "synthesis")
    graph.add_edge("help", "synthesis")

    # Kafka is only used for "both" route - always goes to retrieval next
    graph.add_edge("kafka", "retrieval")

    graph.add_edge("synthesis", END)

    return graph


def compile_graph():
    """Compile the agent graph for execution."""
    graph = create_agent_graph()
    return graph.compile()
