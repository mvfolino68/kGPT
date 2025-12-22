"""Graph construction for the multi-agent system."""

from datetime import datetime
from typing import Literal

from langchain_core.messages import AIMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from kgpt.agents.state import AgentState
from kgpt.llm import get_llm
from kgpt.tools.kafka_tools import get_kafka_tools

# Move tool imports inside functions to avoid circularity with retrieval agents


def get_tools():
    """Get all tools available to the agent."""
    from kgpt.tools.search_tool import search_tool

    return get_kafka_tools() + [search_tool]


def call_model(state: AgentState):
    """
    Core agent node that invokes the LLM.
    Captures reasoning and tool calls for the trace.
    """
    messages = state["messages"]

    # Ensure system message is present
    if not messages or not isinstance(messages[0], SystemMessage):
        from kgpt.agents.prompts import CORE_SYSTEM_PROMPT

        messages = [SystemMessage(content=CORE_SYSTEM_PROMPT)] + messages

    llm = get_llm()
    tools = get_tools()
    model = llm.bind_tools(tools)

    response = model.invoke(messages)

    # Log trace event for educational mode
    trace_event = {
        "agent": "core_agent",
        "status": "completed",
        "timestamp": datetime.now().isoformat(),
        "content": response.content,
        "tool_calls": [tc["name"] for tc in response.tool_calls] if response.tool_calls else [],
    }

    # Append to trace (or initialize list)
    current_trace = state.get("trace_events", []) or []
    current_trace.append(trace_event)

    return {
        "messages": [response],
        "trace_events": current_trace,
        "answer": response.content if not response.tool_calls else "",
    }


def should_continue(state: AgentState) -> Literal["tools", "end"]:
    """Determine flow based on whether tool calls are present."""
    messages = state["messages"]
    last_message = messages[-1]

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return "end"


def create_agent_graph() -> StateGraph:
    """
    Create the ReAct agent graph.
    Structure: START -> agent -> tools -> agent -> END
    """
    graph = StateGraph(AgentState)

    tools = get_tools()
    tool_node = ToolNode(tools)

    graph.add_node("agent", call_model)
    graph.add_node("tools", tool_node)

    graph.set_entry_point("agent")

    graph.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END,
        },
    )

    graph.add_edge("tools", "agent")

    return graph


def compile_graph():
    """Compile the agent graph for execution."""
    graph = create_agent_graph()
    return graph.compile()
