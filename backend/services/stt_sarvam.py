"""
Sarvam Saaras v3 batch Speech-to-Text (English / Hindi / Gujarati / auto).

Buffers PCM frames per utterance and POSTs a WAV to Sarvam when the client
sends `speech_end`. Auto mode uses `language_code=unknown` so Sarvam returns
detected language (hi-IN, gu-IN, en-IN) alongside the transcript.

API: https://docs.sarvam.ai/api-reference-docs/speech-to-text/transcribe
"""
from __future__ import annotations

import io
import logging
import struct
from typing import Awaitable, Callable, Optional

import httpx

from config import (
    SARVAM_STT_LANGUAGE_MAP,
    normalize_detected_language,
    settings,
)

logger = logging.getLogger(__name__)

_SARVAM_STT_URL = "https://api.sarvam.ai/speech-to-text"
_SAMPLE_RATE = 16000
# Skip clips shorter than ~0.3 s — Sarvam auto-detect needs enough signal.
_MIN_PCM_BYTES = int(_SAMPLE_RATE * 0.3 * 2)

TranscriptCallback = Callable[[str, Optional[str]], Awaitable[None]]

_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        common = dict(
            timeout=httpx.Timeout(20.0, connect=4.0),
            limits=httpx.Limits(
                max_keepalive_connections=10, max_connections=20
            ),
            headers={"api-subscription-key": settings.sarvam_api_key},
        )
        try:
            _client = httpx.AsyncClient(http2=True, **common)
        except ImportError:
            logger.warning(
                "h2 not installed — Sarvam STT using HTTP/1.1. "
                "Run: pip install 'httpx[http2]'"
            )
            _client = httpx.AsyncClient(http2=False, **common)
    return _client


def _pcm_to_wav(pcm: bytes, sample_rate: int = _SAMPLE_RATE) -> bytes:
    """Wrap 16-bit mono PCM in a minimal WAV container."""
    channels = 1
    sample_width = 2
    data_size = len(pcm)
    byte_rate = sample_rate * channels * sample_width
    block_align = channels * sample_width
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + data_size,
        b"WAVE",
        b"fmt ",
        16,
        1,
        channels,
        sample_rate,
        byte_rate,
        block_align,
        sample_width * 8,
        b"data",
        data_size,
    )
    return header + pcm


class SarvamSTT:
    """Buffers PCM per utterance and transcribes via Sarvam Saaras v3 REST."""

    def __init__(
        self,
        on_transcript: TranscriptCallback,
        language: str = "auto",
    ) -> None:
        self._on_transcript = on_transcript
        self._language = language
        self._buffer = bytearray()
        self._started = False

    @property
    def language(self) -> str:
        return self._language

    async def start(self) -> None:
        if self._started:
            return
        if not settings.sarvam_api_key:
            raise RuntimeError(
                "SARVAM_API_KEY is not configured — required for Sarvam STT."
            )
        lang_code = SARVAM_STT_LANGUAGE_MAP.get(self._language, "unknown")
        logger.info(
            "Starting Sarvam STT model=%s language=%s (ui=%s)",
            settings.sarvam_stt_model,
            lang_code,
            self._language,
        )
        self._started = True

    async def send_audio(self, pcm_bytes: bytes) -> None:
        if not self._started or not pcm_bytes:
            return
        self._buffer.extend(pcm_bytes)

    async def finalize(self) -> None:
        """POST buffered audio to Sarvam and invoke the transcript callback."""
        if not self._started:
            return

        pcm = bytes(self._buffer)
        self._buffer.clear()

        if len(pcm) < _MIN_PCM_BYTES:
            logger.debug(
                "Sarvam STT skipped short buffer (%d bytes)", len(pcm)
            )
            await self._on_transcript("", None)
            return

        lang_code = SARVAM_STT_LANGUAGE_MAP.get(self._language, "unknown")
        wav = _pcm_to_wav(pcm)

        client = _get_client()
        files = {"file": ("utterance.wav", io.BytesIO(wav), "audio/wav")}
        data = {
            "model": settings.sarvam_stt_model,
            "mode": "transcribe",
            "language_code": lang_code,
        }

        try:
            response = await client.post(_SARVAM_STT_URL, files=files, data=data)
        except httpx.HTTPError as e:
            logger.exception("Sarvam STT request failed: %s", e)
            await self._on_transcript("", None)
            return

        if response.status_code != 200:
            logger.error(
                "Sarvam STT HTTP %s: %s",
                response.status_code,
                response.text[:500],
            )
            await self._on_transcript("", None)
            return

        try:
            payload = response.json()
        except Exception as e:  # noqa: BLE001
            logger.error("Sarvam STT non-JSON response: %s", e)
            await self._on_transcript("", None)
            return

        text = (payload.get("transcript") or "").strip()
        raw_lang = payload.get("language_code")
        detected = normalize_detected_language(raw_lang)
        prob = payload.get("language_probability")

        if text:
            logger.info(
                "Sarvam STT final[%s prob=%s]: %s",
                raw_lang or "?",
                prob,
                text,
            )
        else:
            logger.debug("Sarvam STT returned empty transcript")

        await self._on_transcript(text, detected or raw_lang)

    async def close(self) -> None:
        self._buffer.clear()
        self._started = False


async def start_session(
    on_transcript_callback: TranscriptCallback,
    language: str = "auto",
) -> SarvamSTT:
    stt = SarvamSTT(on_transcript_callback, language=language)
    await stt.start()
    return stt


async def close() -> None:
    global _client
    if _client is not None:
        try:
            await _client.aclose()
        except Exception:  # noqa: BLE001
            pass
        _client = None
