"""Context-aware dynamic prompts (no-speech, errors) using conversation history."""
from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from config import (
    assistant_persona_instruction,
    llm_response_language_instruction,
    settings,
)

logger = logging.getLogger(__name__)

_NO_SPEECH_PROMPT = """You are the LDCE college voice assistant.
{persona_instruction}
The user was silent or we could not hear them.
Based on the conversation so far, generate ONE short spoken line (1-2 sentences) that:
- Politely checks if they are still there
- References what you were discussing if there is history, OR invites them to ask about admissions, courses, fees, hostel, or placement
{lang_instruction}
No markdown. Do not repeat the same wording as previous assistant lines in the history."""


_FALLBACK_PROMPT = """You are the LDCE college voice assistant.
{persona_instruction}
A technical error occurred.
Generate ONE short apology line (1 sentence) and suggest trying again or visiting ldce.ac.in.
{lang_instruction}
Vary wording from: "{avoid}" """


def _lang_instruction(language: str) -> str:
    return llm_response_language_instruction(language)


def _history_snippet(history: list[dict], limit: int = 6) -> str:
    lines = []
    for m in history[-limit:]:
        lines.append(f"{m.get('role', 'user')}: {m.get('content', '')[:200]}")
    return "\n".join(lines) if lines else "(no prior conversation)"


async def generate_no_speech_prompt(
    history: list[dict],
    language: str = "en",
    reason: str = "empty",
    voice_gender: str = "female",
) -> str:
    persona = assistant_persona_instruction(voice_gender, language)
    try:
        llm = ChatGroq(
            model=settings.llm_model,
            api_key=settings.groq_api_key,
            temperature=0.85,
            max_tokens=80,
        )
        resp = await llm.ainvoke(
            [
                SystemMessage(
                    content=_NO_SPEECH_PROMPT.format(
                        persona_instruction=persona,
                        lang_instruction=_lang_instruction(language),
                    )
                ),
                HumanMessage(
                    content=(
                        f"Reason: {reason}\n"
                        f"History:\n{_history_snippet(history)}"
                    )
                ),
            ]
        )
        text = (resp.content or "").strip()
        if text:
            return text
    except Exception as e:  # noqa: BLE001
        logger.warning("Dynamic no-speech failed: %s", e)

    fallbacks_female = {
        "en": "I didn't catch that. Are you still there? Ask me about admission, courses, or fees at LDCE.",
        "hi": "मुझे सुनाई नहीं दिया। क्या आप अभी भी हैं? मैं LDCE में admission, courses या fees के बारे में बता सकती हूँ।",
        "gu": "મને સંભળાયું નહીં. તમે હજી છો? હું LDCE માં admission, courses કે fees વિશે કહી શકું છું.",
    }
    fallbacks_male = {
        "en": "I didn't catch that. Are you still there? Ask me about admission, courses, or fees at LDCE.",
        "hi": "मुझे सुनाई नहीं दिया। क्या आप अभी भी हैं? मैं LDCE में admission, courses या fees के बारे में बता सकता हूँ।",
        "gu": "મને સંભળાયું નહીં. તમે હજી છો? હું LDCE માં admission, courses કે fees વિશે કહી શકું છું.",
    }
    table = fallbacks_female if voice_gender == "female" else fallbacks_male
    lang = language if language in table else "en"
    return table[lang]


async def generate_fallback_message(
    history: list[dict],
    language: str = "en",
    last_error: str = "",
    voice_gender: str = "female",
) -> str:
    persona = assistant_persona_instruction(voice_gender, language)
    avoid = "Sorry, I had trouble with that"
    try:
        llm = ChatGroq(
            model=settings.llm_model,
            api_key=settings.groq_api_key,
            temperature=0.9,
            max_tokens=60,
        )
        resp = await llm.ainvoke(
            [
                SystemMessage(
                    content=_FALLBACK_PROMPT.format(
                        persona_instruction=persona,
                        lang_instruction=_lang_instruction(language),
                        avoid=avoid,
                    )
                ),
                HumanMessage(
                    content=(
                        f"Error: {last_error}\n"
                        f"History:\n{_history_snippet(history, 4)}"
                    )
                ),
            ]
        )
        text = (resp.content or "").strip()
        if text:
            return text
    except Exception as e:  # noqa: BLE001
        logger.warning("Dynamic fallback failed: %s", e)

    fallbacks_female = {
        "en": "Sorry, something went wrong. Please try again or check ldce.ac.in.",
        "hi": "माफ़ कीजिए, कुछ समस्या हुई। कृपया दोबारा कोशिश करें या ldce.ac.in देखें।",
        "gu": "માફ કરજો, થોડી તકલીફ થઈ. ફરી પ્રયાસ કરો અથવા ldce.ac.in જુઓ.",
    }
    fallbacks_male = fallbacks_female
    table = fallbacks_female if voice_gender == "female" else fallbacks_male
    lang = language if language in table else "en"
    return table[lang]
