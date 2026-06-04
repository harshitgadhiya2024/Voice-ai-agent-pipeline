"""
Unified TTS dispatcher.

Routes every sentence to Sarvam Bulbul and yields (pcm_chunk, sample_rate)
tuples so downstream code is engine-agnostic.
"""
from __future__ import annotations

import logging
from typing import AsyncGenerator

from config import TTS_ENGINE_FOR
from services import tts_sarvam

logger = logging.getLogger(__name__)


def engine_for(language: str) -> str:
    return TTS_ENGINE_FOR.get(language, "sarvam")


async def stream_audio(
    text: str, language: str, voice_gender: str = "female"
) -> AsyncGenerator[tuple[bytes, int], None]:
    """Yield (pcm_chunk, sample_rate) tuples for `text` in `language`."""
    async for chunk, sr in tts_sarvam.stream_audio(
        text, language, voice_gender
    ):
        if chunk:
            yield chunk, sr


async def close() -> None:
    await tts_sarvam.close()
