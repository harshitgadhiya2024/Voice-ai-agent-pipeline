"""Use-case-aware streaming LLM entry point — replaces college_llm."""
from __future__ import annotations

import logging
from typing import Any, AsyncGenerator

from langchain_core.messages import AIMessage, HumanMessage

from agents.graph import get_agent_graph
from agents.state import AgentState
from services import dynamic_messages as dynamic_msgs
from services import entities as entity_service
from use_cases import get_use_case

logger = logging.getLogger(__name__)

# Per-session slot store. Keyed by `(use_case_id, session_id)` so a single
# user can switch demos without leaking slot values across them.
_session_slots: dict[tuple[str, str], dict[str, Any]] = {}


def _key(use_case_id: str, session_id: str) -> tuple[str, str]:
    return (use_case_id or "real_estate", session_id or "default")


async def stream_response(
    transcript: str,
    history: list[dict],
    language: str = "en",
    voice_gender: str = "female",
    session_id: str = "default",
    use_case_id: str = "real_estate",
) -> AsyncGenerator[str, None]:
    """Run the use-case graph and yield reply tokens (word-chunked)."""
    use_case = get_use_case(use_case_id)
    graph = get_agent_graph()
    key = _key(use_case.id, session_id)
    slots = _session_slots.setdefault(key, {})

    lc_messages = []
    for m in history[-10:]:
        role = m.get("role", "user")
        content = m.get("content", "")
        if not content:
            continue
        if role == "assistant":
            lc_messages.append(AIMessage(content=content))
        else:
            lc_messages.append(HumanMessage(content=content))
    lc_messages.append(HumanMessage(content=transcript))

    initial: AgentState = {
        "messages": lc_messages,
        "language": language,
        "voice_gender": voice_gender,
        "use_case_id": use_case.id,
        "user_input": transcript,
        "active_intent": use_case.intents[0].id,
        "slots": dict(slots),
        "missing_slots": [],
        "entities": [],
        "needs_clarification": False,
        "reply": "",
        "turn_entities": [],
    }

    try:
        result = await graph.ainvoke(initial)
    except Exception as e:  # noqa: BLE001
        logger.exception("Agent graph failed (use_case=%s): %s", use_case.id, e)
        fallback = await dynamic_msgs.generate_fallback_message(
            history, language, str(e), voice_gender=voice_gender
        )
        for word in fallback.split():
            yield word + " "
        return

    new_slots = dict(result.get("slots", {}))
    new_slots["last_intent"] = result.get("active_intent", use_case.intents[0].id)
    _session_slots[key] = new_slots

    reply = (result.get("reply") or "").strip()
    if not reply:
        reply = await dynamic_msgs.generate_fallback_message(
            history, language, voice_gender=voice_gender
        )

    words = reply.split()
    for i, word in enumerate(words):
        yield word + (" " if i < len(words) - 1 else "")


async def build_session_report(
    history: list[dict],
    session_id: str = "default",
    use_case_id: str = "real_estate",
) -> dict[str, Any]:
    """Entity extraction + report payload for frontend after a call ends."""
    use_case = get_use_case(use_case_id)
    key = _key(use_case.id, session_id)
    slots = _session_slots.get(key, {})

    extracted = await entity_service.extract_entities(
        history, slots, use_case.id
    )
    return {
        "use_case_id": use_case.id,
        "use_case_name": use_case.name,
        "company": use_case.company,
        # Backward-compat fields for the existing SessionReport UI.
        "college_id": use_case.id,
        "college_name": f"{use_case.name} — {use_case.company}",
        "conversation": history,
        "slots": slots,
        "entities": extracted.get("entities", []),
        "summary": extracted.get("summary", ""),
        "primary_intent": extracted.get(
            "primary_intent", slots.get("last_intent", "general")
        ),
        "turn_count": len([m for m in history if m.get("role") == "user"]),
    }


def clear_session(session_id: str = "default", use_case_id: str | None = None) -> None:
    if use_case_id:
        _session_slots.pop(_key(use_case_id, session_id), None)
        return
    # Clear across all use cases for this session id.
    for k in list(_session_slots.keys()):
        if k[1] == session_id:
            _session_slots.pop(k, None)
