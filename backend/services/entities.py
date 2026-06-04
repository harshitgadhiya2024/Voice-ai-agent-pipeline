"""Extract entities from conversation for session reports."""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from config import settings

logger = logging.getLogger(__name__)

_EXTRACT_PROMPT = """Extract structured entities from this college voicebot conversation.
Return ONLY JSON:
{
  "entities": [
    {"type": "program_level|branch|student_category|topic|contact_intent|other", "value": "...", "confidence": 0.0-1.0}
  ],
  "summary": "one sentence summary of what the user wanted",
  "primary_intent": "fees|admissions|courses|placement|hostel|facilities|general"
}
"""


async def extract_entities(
    history: list[dict],
    slots: dict[str, Any],
    college_id: str = "ldce",
) -> dict[str, Any]:
    """Build entity list + summary from full conversation."""
    convo = ""
    for m in history[-20:]:
        convo += f"{m.get('role', 'user')}: {m.get('content', '')}\n"
    convo += f"\nCollected slots: {json.dumps(slots, ensure_ascii=False)}"

    try:
        llm = ChatGroq(
            model=settings.llm_model,
            api_key=settings.groq_api_key,
            temperature=0.2,
            max_tokens=400,
        )
        resp = await llm.ainvoke(
            [
                SystemMessage(content=_EXTRACT_PROMPT),
                HumanMessage(content=convo),
            ]
        )
        text = (resp.content or "").strip()
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return json.loads(match.group(0))
    except Exception as e:  # noqa: BLE001
        logger.warning("Entity extraction failed: %s", e)

    entities = [
        {"type": k, "value": str(v), "confidence": 1.0}
        for k, v in slots.items()
    ]
    return {
        "entities": entities,
        "summary": "College voice assistant session",
        "primary_intent": slots.get("last_agent", "general"),
        "college_id": college_id,
    }
