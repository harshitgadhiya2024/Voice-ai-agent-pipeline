"""LLM entry point — dispatches to the use-case-aware agent graph."""
from __future__ import annotations

from typing import AsyncGenerator

from services import agent_llm


async def stream_response(
    transcript: str,
    history: list[dict],
    language: str = "auto",
    voice_gender: str = "female",
    session_id: str = "default",
    use_case_id: str = "real_estate",
) -> AsyncGenerator[str, None]:
    async for token in agent_llm.stream_response(
        transcript,
        history,
        language=language,
        voice_gender=voice_gender,
        session_id=session_id,
        use_case_id=use_case_id,
    ):
        yield token
