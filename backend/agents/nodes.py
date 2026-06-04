"""Generic LangGraph nodes — config-driven, work for every use case."""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from config import (
    assistant_persona_instruction,
    llm_response_language_instruction,
    settings,
)
from use_cases import UseCase, get_use_case

logger = logging.getLogger(__name__)


_ROUTER_PROMPT = """You are the routing brain for the {use_case_name} voice assistant ({company}).
Your job is agentic triage: pick the best specialist intent, extract every slot
the user already stated (city, ID, date, product, etc.), and list only slots still
needed for a precise answer from the knowledge base.

Classify the user's message into exactly ONE intent from this list:
{intents}

Extract slot values the user already mentioned, from this list:
{slots}

If the message is vague, choose the closest intent and put uncertain slots in
missing_slots. Prefer intents that match location-specific queries when a city
or branch is named.

Reply with ONLY a single JSON object (no prose, no markdown):
{{"intent": "<one intent id>", "slots": {{"<slot_id>": "<value>"}}, "missing_slots": ["<slot_id>", ...]}}
"""

_AGENT_PROMPT = """You are the {intent_label} specialist for {company} ({use_case_name}).
Use ONLY the knowledge JSON below. If something specific isn't in the knowledge,
say so politely and offer to connect to a human teammate or share the contact
details — never invent prices, dates, IDs, or policies.

Knowledge:
{context}

Information collected from the user so far: {slots}

Disclaimer to keep in mind: {disclaimer}

Rules:
- {persona_instruction}
- {language_instruction}
- Voice-friendly: 1-3 short spoken sentences — sound like a real human on a phone call, not an essay.
- No markdown, lists, or bullet points.
- If the user mixes Hindi/Gujarati/English, reply in the same natural mixed style.
- If the user asks for something outside the knowledge or the company's scope, redirect kindly.
"""

_CLARIFY_PROMPT = """You are the {use_case_name} voice assistant for {company}.
{persona_instruction}
The user is asking about {intent_label} but you still need: {missing}.
Ask ONE short, friendly follow-up question to capture that detail. Use the
prior conversation for context.
{language_instruction}
No markdown. 1-2 spoken sentences max."""


def _llm(temperature: float = 0.4, max_tokens: int = 256) -> ChatGroq:
    return ChatGroq(
        model=settings.llm_model,
        api_key=settings.groq_api_key,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def _intent_block(use_case: UseCase) -> str:
    return "\n".join(
        f"- {i.id}: {i.description}" for i in use_case.intents
    )


def _slot_block(use_case: UseCase) -> str:
    if not use_case.slots:
        return "(no slots defined)"
    return "\n".join(
        f"- {s.id}: {s.question}" for s in use_case.slots.values()
    )


def _parse_router_json(text: str) -> dict[str, Any]:
    text = (text or "").strip()
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        text = match.group(0)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def _history_text(state: dict, limit: int = 6) -> str:
    out = []
    for m in state.get("messages", [])[-limit:]:
        role = getattr(m, "type", None) or m.get("role", "user")
        content = getattr(m, "content", None) or m.get("content", "")
        if content:
            out.append(f"{role}: {content}")
    return "\n".join(out)


# ---------- Nodes ----------

async def router_node(state: dict) -> dict:
    use_case = get_use_case(state.get("use_case_id", ""))
    history = _history_text(state, limit=6)

    prompt = _ROUTER_PROMPT.format(
        use_case_name=use_case.name,
        company=use_case.company,
        intents=_intent_block(use_case),
        slots=_slot_block(use_case),
    )
    user_block = (
        f"Conversation:\n{history}\n"
        f"Latest user message: {state.get('user_input', '')}\n"
        f"Existing slots: {json.dumps(state.get('slots', {}), ensure_ascii=False)}"
    )

    try:
        resp = await _llm(temperature=0.1, max_tokens=200).ainvoke(
            [SystemMessage(content=prompt), HumanMessage(content=user_block)]
        )
        parsed = _parse_router_json(resp.content or "")
    except Exception as e:  # noqa: BLE001
        logger.warning("Router LLM failed (%s) — defaulting to general", e)
        parsed = {}

    intent = parsed.get("intent", "general")
    if intent not in use_case.intent_ids:
        intent = use_case.intents[0].id

    new_slots = {**state.get("slots", {}), **(parsed.get("slots") or {})}
    new_slots = {k: v for k, v in new_slots.items() if v}

    required = use_case.required_slots(intent)
    missing = [s for s in required if s not in new_slots]
    for s in parsed.get("missing_slots", []) or []:
        if s in required and s not in missing:
            missing.append(s)

    return {
        "active_intent": intent,
        "slots": new_slots,
        "missing_slots": missing,
        "needs_clarification": len(missing) > 0,
    }


async def clarify_node(state: dict) -> dict:
    use_case = get_use_case(state.get("use_case_id", ""))
    missing = state.get("missing_slots") or []
    if not missing:
        return {"needs_clarification": False, "reply": ""}

    slot_id = missing[0]
    fallback_q = use_case.slot_question(slot_id)

    lang = state.get("language", "en")
    voice_gender = state.get("voice_gender", "female")
    persona = assistant_persona_instruction(
        voice_gender,
        lang,
        agent_female=use_case.persona_name_female,
        agent_male=use_case.persona_name_male,
        role=f"{use_case.name.lower()} voice assistant for {use_case.company}",
    )
    intent = use_case.find_intent(state.get("active_intent", "general"))

    try:
        resp = await _llm(temperature=0.55, max_tokens=120).ainvoke(
            [
                SystemMessage(
                    content=_CLARIFY_PROMPT.format(
                        use_case_name=use_case.name,
                        company=use_case.company,
                        persona_instruction=persona,
                        intent_label=intent.label,
                        missing=slot_id.replace("_", " "),
                        language_instruction=llm_response_language_instruction(lang),
                    )
                ),
                HumanMessage(
                    content=(
                        f"User said: {state.get('user_input', '')}\n"
                        f"Suggested question template: {fallback_q}"
                    )
                ),
            ]
        )
        reply = (resp.content or fallback_q).strip()
    except Exception as e:  # noqa: BLE001
        logger.warning("Clarify LLM failed (%s) — using template", e)
        reply = fallback_q

    return {"reply": reply, "needs_clarification": True}


async def specialist_node(state: dict) -> dict:
    use_case = get_use_case(state.get("use_case_id", ""))
    intent_id = state.get("active_intent", use_case.intents[0].id)
    intent = use_case.find_intent(intent_id)

    lang = state.get("language", "en")
    voice_gender = state.get("voice_gender", "female")
    persona = assistant_persona_instruction(
        voice_gender,
        lang,
        agent_female=use_case.persona_name_female,
        agent_male=use_case.persona_name_male,
        role=f"{use_case.name.lower()} voice assistant for {use_case.company}",
    )
    # Combine the use case's bespoke persona with the gender/language guard.
    persona = f"{use_case.persona}\n\n{persona}"

    prompt = _AGENT_PROMPT.format(
        intent_label=intent.label,
        company=use_case.company,
        use_case_name=use_case.name,
        context=use_case.context_for_intent(
            intent_id, state.get("slots", {})
        ),
        slots=json.dumps(state.get("slots", {}), ensure_ascii=False),
        disclaimer=use_case.fallback_disclaimer,
        persona_instruction=persona,
        language_instruction=llm_response_language_instruction(lang),
    )

    try:
        resp = await _llm(temperature=0.45, max_tokens=320).ainvoke(
            [
                SystemMessage(content=prompt),
                HumanMessage(
                    content=(
                        f"Recent conversation:\n{_history_text(state, limit=8)}\n"
                        f"User: {state.get('user_input', '')}"
                    )
                ),
            ]
        )
        reply = (resp.content or "").strip()
    except Exception as e:  # noqa: BLE001
        logger.exception("Specialist node failed: %s", e)
        reply = (
            f"I'm sorry, I had trouble pulling that up just now. "
            f"You can also reach {use_case.company} directly. Could you try "
            f"again?"
        )

    return {"reply": reply, "needs_clarification": False}


def route_after_router(state: dict) -> str:
    if state.get("needs_clarification"):
        return "clarify"
    return "specialist"
