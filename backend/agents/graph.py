"""Generic LangGraph runtime — single graph, dispatches by use_case_id."""
from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, StateGraph

from agents.nodes import (
    clarify_node,
    router_node,
    route_after_router,
    specialist_node,
)
from agents.state import AgentState


def _build_graph():
    g = StateGraph(AgentState)
    g.add_node("router", router_node)
    g.add_node("clarify", clarify_node)
    g.add_node("specialist", specialist_node)

    g.set_entry_point("router")
    g.add_conditional_edges(
        "router",
        route_after_router,
        {
            "clarify": "clarify",
            "specialist": "specialist",
        },
    )
    g.add_edge("clarify", END)
    g.add_edge("specialist", END)
    return g.compile()


@lru_cache(maxsize=1)
def get_agent_graph():
    return _build_graph()


# Backwards-compat alias for older imports.
def get_college_graph():
    return get_agent_graph()
