"""LangGraph orchestration for the multi-agent system."""

from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from loguru import logger

from kgpt.llm import get_llm
from kgpt.tools.kafka_tools import get_kafka_tools

# --- State Definition (formerly state.py) ---


class AgentState(TypedDict):
    """State shared between all agents in the graph."""

    # The user's original question
    question: str

    # Message history (standard ReAct)
    messages: Annotated[list, add_messages]

    # --- Core Output Fields ---
    # The final synthesized answer
    answer: str
    # Source citations
    citations: list[dict]
    # Error message if something went wrong
    error: str | None
    # Educational mode trace events
    trace_events: list[dict]


# --- Graph Construction (formerly graph_builder.py) ---


def get_tools():
    """Get all tools available to the agent."""
    from kgpt.tools.query_enhancer import query_enhancer_tool
    from kgpt.tools.search_tool import search_tool

    # Return all tools: Kafka + Search + QueryEnhancer
    return get_kafka_tools() + [search_tool, query_enhancer_tool]


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
    # Bind tools to the model
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


# --- Orchestrator (formerly existing graph.py logic) ---


class AgentOrchestrator:
    """High-level orchestrator for the multi-agent system."""

    def __init__(self):
        """Initialize the orchestrator."""
        self._compiled_graph = None

    @property
    def graph(self):
        """Lazy-load the compiled graph."""
        if self._compiled_graph is None:
            self._compiled_graph = compile_graph()
        return self._compiled_graph

    async def query(
        self,
        question: str,
        chat_history: list | None = None,
    ) -> dict:
        """
        Process a question through the agent pipeline.
        """
        logger.info(f"Processing question: {question[:100]}...")

        # Build initial state
        messages = []
        if chat_history:
            for msg in chat_history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                else:
                    messages.append(AIMessage(content=msg["content"]))

        messages.append(HumanMessage(content=question))

        initial_state: AgentState = {
            "question": question,
            "messages": messages,
            "answer": "",
            "citations": [],
            "error": None,
            "trace_events": [],
        }

        # Run the graph
        try:
            result = await self.graph.ainvoke(initial_state)

            return {
                "answer": result.get("answer", "I couldn't generate an answer."),
                "citations": result.get("citations", []),
                "error": result.get("error"),
            }

        except Exception as e:
            logger.error(f"Agent orchestration error: {e}")
            return {
                "answer": f"I encountered an error processing your question: {str(e)}",
                "citations": [],
                "error": str(e),
            }

    async def query_stream(
        self,
        question: str,
        chat_history: list | None = None,
    ) -> AsyncGenerator[str | dict, None]:
        """
        Process a question with streaming output.
        """
        async for chunk in self.query_stream_with_stages(question, chat_history):
            yield chunk

    async def query_stream_with_stages(
        self,
        question: str,
        chat_history: list | None = None,
    ) -> AsyncGenerator[str | dict, None]:
        """
        Process a question with streaming output, stage updates, and agent activity events.
        """
        from kgpt.agents.streaming import query_stream_with_stages

        # Note: query_stream_with_stages is imported from streaming.py
        # We pass self.graph to it
        async for chunk in query_stream_with_stages(question, chat_history, self.graph):
            yield chunk


# Singleton orchestrator
_orchestrator: AgentOrchestrator | None = None


def get_orchestrator() -> AgentOrchestrator:
    """Get the singleton orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator
