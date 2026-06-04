"""LangGraph state for the multi-use-case Voice AI agents."""
from __future__ import annotations

from typing import Annotated, Any

from typing_extensions import TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    """Shared state for the use-case-driven LangGraph runtime."""

    messages: Annotated[list, add_messages]
    language: str
    voice_gender: str
    use_case_id: str
    user_input: str
    active_intent: str
    slots: dict[str, Any]
    missing_slots: list[str]
    entities: list[dict[str, Any]]
    needs_clarification: bool
    reply: str
    turn_entities: list[dict[str, Any]]


# Backwards-compat alias for older imports.
CollegeAgentState = AgentState
