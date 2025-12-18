"""Graph construction for the multi-agent system."""

from langgraph.graph import END, StateGraph

from kgpt.agents.admin import admin_node
from kgpt.agents.kafka_agent import kafka_node
from kgpt.agents.retrieval import retrieval_node
from kgpt.agents.router import route_decision, router_node
from kgpt.agents.state import AgentState
from kgpt.agents.synthesis import synthesis_node


def create_agent_graph() -> StateGraph:
    """
    Create the multi-agent graph.

    Graph structure:
        START -> router -> [retrieval | kafka | admin | synthesis] -> ... -> synthesis -> END

    Routes:
    - "retrieval": docs only -> retrieval -> synthesis
    - "kafka": cluster only -> kafka -> synthesis
    - "admin": admin operation -> admin -> synthesis
    - "both": cluster + docs -> kafka -> retrieval -> synthesis
    - "direct": simple response -> synthesis
    """
    # Create the graph
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("router", router_node)
    graph.add_node("retrieval", retrieval_node)
    graph.add_node("kafka", kafka_node)
    graph.add_node("admin", admin_node)
    graph.add_node("synthesis", synthesis_node)

    # Set entry point
    graph.set_entry_point("router")

    # Add conditional edges from router
    graph.add_conditional_edges(
        "router",
        route_decision,
        {
            "retrieval": "retrieval",
            "kafka": "kafka",
            "admin": "admin",
            "synthesis": "synthesis",  # Direct route
        },
    )

    # Retrieval -> Synthesis (no more validation step)
    graph.add_edge("retrieval", "synthesis")

    # Admin -> Synthesis
    graph.add_edge("admin", "synthesis")

    # Kafka -> Retrieval (if needs_retrieval) or Synthesis (if kafka-only)
    def kafka_next_node(state: AgentState) -> str:
        """Determine next node after kafka based on routing."""
        if state.get("needs_retrieval"):
            return "retrieval"
        return "synthesis"

    graph.add_conditional_edges(
        "kafka",
        kafka_next_node,
        {
            "retrieval": "retrieval",
            "synthesis": "synthesis",
        },
    )

    # Synthesis -> END
    graph.add_edge("synthesis", END)

    return graph


def compile_graph():
    """Compile the agent graph for execution."""
    graph = create_agent_graph()
    return graph.compile()
