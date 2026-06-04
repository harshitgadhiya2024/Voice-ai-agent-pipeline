"""
Sarvam AI TTS service (English / Hindi / Gujarati).

Latency optimisations:
- Shared HTTP/2 client with keep-alive (no TCP handshake per sentence)
- bulbul:v2 model (fastest Sarvam model, ~150-250ms TTFB for short text)
- 22050 Hz sample rate (lower = faster to synthesise than 24kHz)
- `enable_preprocessing=False` (skips text-normalisation overhead)
- WAV header is parsed and stripped server-side so the client only receives
  raw linear16 PCM. The full audio is then
  chunked into 4KB frames and yielded for streaming playback.

API: https://docs.sarvam.ai/api-reference-docs/text-to-speech/convert
"""
from __future__ import annotations

import base64
import logging
import struct
from typing import AsyncGenerator, Optional

import httpx

from config import SARVAM_LANGUAGE_CODE, sarvam_voice_for, settings

logger = logging.getLogger(__name__)

_SARVAM_URL = "https://api.sarvam.ai/text-to-speech"
_CHUNK_SIZE = 4096  # bytes per yielded PCM chunk

_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        common = dict(
            timeout=httpx.Timeout(20.0, connect=4.0),
            limits=httpx.Limits(
                max_keepalive_connections=10, max_connections=20
            ),
            headers={
                "api-subscription-key": settings.sarvam_api_key,
                "Content-Type": "application/json",
            },
        )
        try:
            _client = httpx.AsyncClient(http2=True, **common)
        except ImportError:
            logger.warning(
                "h2 not installed — Sarvam TTS using HTTP/1.1. "
                "Run: pip install 'httpx[http2]'"
            )
            _client = httpx.AsyncClient(http2=False, **common)
    return _client


def _parse_wav(wav: bytes) -> tuple[bytes, int]:
    """Return (raw_pcm, sample_rate) given a WAV-encoded buffer.

    Robust to extra chunks before the `data` chunk (LIST, fact, etc.).
    Falls back to (input, configured_rate) if the buffer isn't a WAV.
    """
    if len(wav) < 44 or wav[:4] != b"RIFF" or wav[8:12] != b"WAVE":
        logger.debug("Sarvam payload is not a WAV; assuming raw PCM")
        return wav, settings.sarvam_sample_rate

    try:
        sample_rate = struct.unpack_from("<I", wav, 24)[0]
    except struct.error:
        sample_rate = settings.sarvam_sample_rate

    offset = 12
    while offset + 8 <= len(wav):
        chunk_id = wav[offset : offset + 4]
        chunk_size = struct.unpack_from("<I", wav, offset + 4)[0]
        if chunk_id == b"data":
            start = offset + 8
            return wav[start : start + chunk_size], sample_rate
        offset += 8 + chunk_size

    return wav[44:], sample_rate


async def synthesize(
    text: str, language: str, voice_gender: str = "female"
) -> tuple[bytes, int]:
    """One-shot synthesise. Returns (raw_pcm_bytes, sample_rate)."""
    text = (text or "").strip()
    if not text:
        return b"", settings.sarvam_sample_rate
    if not settings.sarvam_api_key:
        raise RuntimeError(
            "SARVAM_API_KEY is not configured — required for Sarvam TTS."
        )

    speaker = sarvam_voice_for(voice_gender)
    model = settings.sarvam_model
    lang_code = SARVAM_LANGUAGE_CODE.get(language, "hi-IN")

    body: dict = {
        "text": text,
        "target_language_code": lang_code,
        "speaker": speaker,
        "model": model,
        "speech_sample_rate": settings.sarvam_sample_rate,
        "pace": settings.sarvam_pace,
    }
    # bulbul:v2-only params — omitted for v3 to avoid API errors
    if not model.startswith("bulbul:v3"):
        body["pitch"] = settings.sarvam_pitch
        body["loudness"] = settings.sarvam_loudness
        body["enable_preprocessing"] = False

    logger.info(
        "Sarvam TTS model=%s speaker=%s lang=%s gender=%s",
        model,
        speaker,
        lang_code,
        voice_gender,
    )

    client = _get_client()
    try:
        response = await client.post(_SARVAM_URL, json=body)
    except httpx.HTTPError as e:
        logger.exception("Sarvam request failed: %s", e)
        raise

    if response.status_code != 200:
        # Some Sarvam deployments still use the older field name `inputs`
        # (a list). Retry once with that shape before giving up.
        if response.status_code in (400, 422):
            try:
                retry_body = dict(body)
                retry_body.pop("text", None)
                retry_body["inputs"] = [text]
                response = await client.post(_SARVAM_URL, json=retry_body)
            except httpx.HTTPError as e:
                logger.exception("Sarvam retry failed: %s", e)
                raise
        if response.status_code != 200:
            text_err = response.text[:500]
            logger.error(
                "Sarvam TTS HTTP %s: %s", response.status_code, text_err
            )
            raise RuntimeError(
                f"Sarvam TTS failed ({response.status_code}): {text_err}"
            )

    try:
        data = response.json()
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"Sarvam returned non-JSON: {e}") from e

    audios = data.get("audios") or []
    if not audios:
        # Some responses key on `audio` (singular)
        single = data.get("audio")
        if single:
            audios = [single]
    if not audios:
        raise RuntimeError("Sarvam returned no audio payload")

    try:
        wav_bytes = base64.b64decode(audios[0])
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"Sarvam audio not valid base64: {e}") from e

    pcm, sr = _parse_wav(wav_bytes)
    return pcm, sr


async def stream_audio(
    text: str, language: str, voice_gender: str = "female"
) -> AsyncGenerator[tuple[bytes, int], None]:
    """
    Yield (pcm_chunk, sample_rate) tuples for the synthesised audio.

    Sarvam's REST endpoint is one-shot (not chunk-streaming), so we
    synthesise the full sentence then yield 4KB PCM frames so the client
    playback queue can start as soon as the first frame arrives.
    """
    try:
        pcm, sr = await synthesize(text, language, voice_gender)
    except Exception as e:  # noqa: BLE001
        logger.exception("Sarvam stream_audio failure: %s", e)
        return
    for i in range(0, len(pcm), _CHUNK_SIZE):
        yield pcm[i : i + _CHUNK_SIZE], sr


async def close() -> None:
    global _client
    if _client is not None:
        try:
            await _client.aclose()
        except Exception:  # noqa: BLE001
            pass
        _client = None
