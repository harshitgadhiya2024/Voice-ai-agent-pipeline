"""
WebSocket endpoint — college voicebot pipeline:

    [Browser PCM] -> Sarvam STT -> LangGraph college agents -> Sarvam TTS
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import time
import uuid
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from config import SUPPORTED_LANGUAGES, TTS_ENGINE_FOR, settings, tts_voice_metadata
from services import agent_llm, college_llm  # college_llm is now an alias
from services import dynamic_messages as dynamic_msgs
from services import stt_sarvam as stt_service
from services import llm as llm_service
from services import tts_router as tts_service
from use_cases import DEFAULT_USE_CASE_ID, get_use_case, list_use_cases

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/use_cases")
async def get_use_cases() -> dict:
    """Public catalogue for the frontend gallery."""
    return {"use_cases": list_use_cases()}


@router.get("/use_cases/{use_case_id}")
async def get_one_use_case(use_case_id: str) -> dict:
    uc = get_use_case(use_case_id)
    return uc.to_metadata()

# Sentence boundary covering English + Devanagari/Gujarati danda (।)
_SENTENCE_BOUNDARY = re.compile(r"([\.!\?।])(\s+|$)")
# Smaller for non-English to fire TTS sooner — Sarvam's TTFB is ~200ms so
# we want to get the first sentence out as soon as we can.
_MIN_SENTENCE_CHARS = 4
# Comma-level boundary for the *first* chunk — lower = earlier first audio.
_SOFT_BOUNDARY = re.compile(r"([,;:])\s")
_SOFT_BOUNDARY_MIN_CHARS = 8
# Fire first TTS once we have enough tokens even without punctuation.
_FIRST_AUDIO_MIN_CHARS = 14
_FIRST_AUDIO_MAX_CHARS = 28


def _early_first_chunk(buffer: str) -> tuple[str, str] | None:
    """Split an early speakable head from `buffer` at a word boundary."""
    if len(buffer) < _FIRST_AUDIO_MIN_CHARS:
        return None
    end = min(len(buffer), _FIRST_AUDIO_MAX_CHARS)
    split = buffer.rfind(" ", 0, end)
    if split < 8:
        return None
    head = buffer[:split].strip()
    if not head:
        return None
    return head, buffer[split + 1 :]


class VoiceSession:
    def __init__(self, websocket: WebSocket) -> None:
        self.ws = websocket
        self.history: list[dict] = []
        # Sarvam batch STT session (buffers PCM per utterance).
        self.stt: Optional[stt_service.SarvamSTT] = None
        self.transcript_queue: asyncio.Queue[tuple[str, Optional[str]]] = (
            asyncio.Queue()
        )
        self.worker_task: Optional[asyncio.Task] = None
        self._pipeline_lock = asyncio.Lock()
        self._closed = False
        self.language: str = settings.default_language
        _default_uc = get_use_case(DEFAULT_USE_CASE_ID)
        self.voice_gender: str = _default_uc.default_voice_gender or "female"
        self.session_id: str = str(uuid.uuid4())
        # Active use case (defaults to first demo). Frontend sends `set_use_case`
        # before the first turn to pick a different one.
        self.use_case_id: str = DEFAULT_USE_CASE_ID
        # Last language Sarvam detected — used for auto-mode prompts.
        self.last_detected_language: Optional[str] = None
        # Set while waiting for Sarvam to return a transcript after
        # `speech_end`. Resolved by `_on_transcript` or timed out.
        self._transcript_waiter: Optional[asyncio.Future[None]] = None
        self._got_transcript_this_turn = False

    # ---------- WebSocket send helpers ----------

    async def send_json(self, payload: dict) -> None:
        if self._closed:
            return
        try:
            await self.ws.send_text(json.dumps(payload, ensure_ascii=False))
        except (WebSocketDisconnect, RuntimeError) as e:
            self._closed = True
            logger.debug("send_json after close: %s", e)
        except Exception as e:  # noqa: BLE001
            logger.debug("send_json failed: %s", e)

    async def send_binary(self, data: bytes) -> None:
        if self._closed or not data:
            return
        try:
            await self.ws.send_bytes(data)
        except (WebSocketDisconnect, RuntimeError) as e:
            self._closed = True
            logger.debug("send_binary after close: %s", e)
        except Exception as e:  # noqa: BLE001
            logger.debug("send_binary failed: %s", e)

    # ---------- Pipeline callbacks ----------

    async def _on_transcript(
        self, text: str, detected_language: Optional[str]
    ) -> None:
        waiter = self._transcript_waiter
        if waiter is not None and not waiter.done():
            waiter.set_result(None)

        text = (text or "").strip()
        if not text:
            return

        self._got_transcript_this_turn = True
        if detected_language:
            self.last_detected_language = detected_language
        await self.send_json(
            {
                "type": "transcript",
                "text": text,
                "language": detected_language,
            }
        )
        await self.transcript_queue.put((text, detected_language))

    def _resolve_prompt_language(self) -> str:
        """Language for canned prompts (no-speech help, etc.)."""
        if self.language in ("en", "hi", "gu"):
            return self.language
        detected = self.last_detected_language
        if detected:
            d = detected.lower()
            if d.startswith("hi"):
                return "hi"
            if d.startswith("gu"):
                return "gu"
            if d.startswith("en"):
                return "en"
        return "en"

    async def _speak_fixed_message(self, text: str, lang: str) -> None:
        """Speak a short canned line via TTS (no LLM)."""
        text = (text or "").strip()
        if not text:
            return

        engine = TTS_ENGINE_FOR.get(lang, "sarvam")
        sample_rate = settings.sarvam_sample_rate

        await self.send_json({"type": "llm_token", "text": text})
        await self.send_json(
            {
                "type": "tts_start",
                "engine": engine,
                "language": lang,
                "sample_rate": sample_rate,
                "voice_gender": self.voice_gender,
                **tts_voice_metadata(self.voice_gender, engine),
            }
        )

        got_audio = False
        async for pcm, sr in tts_service.stream_audio(
            text, lang, self.voice_gender
        ):
            if pcm:
                got_audio = True
                await self.send_binary(pcm)

        if not got_audio:
            logger.warning(
                "TTS produced no audio for prompt (engine=%s, lang=%s) — "
                "falling back to browser speech",
                engine,
                lang,
            )
            await self.send_json(
                {"type": "tts_text", "text": text, "language": lang}
            )

        await self.send_json({"type": "tts_end"})

    async def _emit_no_speech(self, reason: str = "empty") -> None:
        """Speak a context-aware prompt when STT produced nothing."""
        lang = self._resolve_prompt_language()
        prompt = await dynamic_msgs.generate_no_speech_prompt(
            self.history, lang, reason, voice_gender=self.voice_gender
        )
        logger.info(
            "No speech detected (%s) — speaking prompt in %s", reason, lang
        )
        await self._speak_fixed_message(prompt, lang)
        await self.send_json(
            {
                "type": "no_speech",
                "reason": reason,
                "message": prompt,
                "language": lang,
            }
        )

    # ---------- Worker ----------

    async def _worker_loop(self) -> None:
        while not self._closed:
            try:
                transcript, detected = await self.transcript_queue.get()
            except asyncio.CancelledError:
                break
            try:
                async with self._pipeline_lock:
                    await self._run_turn(transcript, detected)
            except asyncio.CancelledError:
                break
            except Exception as e:  # noqa: BLE001
                logger.exception("Worker error: %s", e)
                await self.send_json(
                    {"type": "error", "message": f"Pipeline error: {e}"}
                )

    def _resolve_reply_language(self, detected: Optional[str]) -> str:
        """Pick the language we should reply in for this turn."""
        if self.language in ("en", "hi", "gu"):
            return self.language
        # auto
        if detected:
            d = detected.lower()
            if d.startswith("en"):
                return "en"
            if d.startswith("hi"):
                return "hi"
            if d.startswith("gu"):
                return "gu"
        return "en"

    async def _run_turn(
        self, transcript: str, detected: Optional[str]
    ) -> None:
        await self.send_json({"type": "status", "status": "thinking"})

        reply_lang = self._resolve_reply_language(detected)
        engine = TTS_ENGINE_FOR.get(reply_lang, "sarvam")
        voice_gender = self.voice_gender
        sentence_queue: asyncio.Queue[Optional[str]] = asyncio.Queue()
        full_reply_parts: list[str] = []
        first_sentence_sent = False
        tts_announced = False

        def _spawn_tts(sentence: str) -> None:
            nonlocal first_sentence_sent, tts_announced
            if not sentence:
                return
            sentence_queue.put_nowait(sentence)
            first_sentence_sent = True
            # Announce TTS immediately so UI flips to "speaking" without
            # waiting for the first audio bytes to arrive.
            if not tts_announced:
                sample_rate = settings.sarvam_sample_rate
                asyncio.create_task(
                    self.send_json(
                        {
                            "type": "tts_start",
                            "engine": engine,
                            "language": reply_lang,
                            "sample_rate": sample_rate,
                            "voice_gender": voice_gender,
                            **tts_voice_metadata(voice_gender, engine),
                        }
                    )
                )
                tts_announced = True

        # ----- LLM producer -----
        async def llm_producer() -> None:
            buffer = ""
            try:
                async for token in llm_service.stream_response(
                    transcript,
                    self.history,
                    language=reply_lang,
                    voice_gender=voice_gender,
                    session_id=self.session_id,
                    use_case_id=self.use_case_id,
                ):
                    if not token:
                        continue
                    full_reply_parts.append(token)
                    buffer += token
                    asyncio.create_task(
                        self.send_json({"type": "llm_token", "text": token})
                    )

                    # Hard sentence boundaries → fire TTS immediately.
                    # We only split when the boundary is at least
                    # `_MIN_SENTENCE_CHARS` deep into the buffer; otherwise
                    # we keep accumulating tokens instead of mutating the
                    # buffer (which previously caused short fragments to be
                    # lost or re-matched forever).
                    while True:
                        match = _SENTENCE_BOUNDARY.search(buffer)
                        if not match:
                            break
                        end = match.end()
                        if end < _MIN_SENTENCE_CHARS:
                            # The boundary sits too early; wait for more
                            # tokens so the chunk grows past the minimum.
                            break
                        sentence = buffer[:end].strip()
                        buffer = buffer[end:]
                        if sentence:
                            _spawn_tts(sentence)

                    # First chunk: comma boundary, then word-boundary fallback
                    # so the user hears audio before a full sentence forms.
                    if not first_sentence_sent:
                        if len(buffer) >= _SOFT_BOUNDARY_MIN_CHARS:
                            soft = _SOFT_BOUNDARY.search(buffer)
                            if soft:
                                end = soft.end()
                                if end >= _SOFT_BOUNDARY_MIN_CHARS:
                                    head = buffer[:end].strip()
                                    buffer = buffer[end:]
                                    if head:
                                        _spawn_tts(head)
                        if not first_sentence_sent:
                            early = _early_first_chunk(buffer)
                            if early:
                                head, buffer = early
                                _spawn_tts(head)

            finally:
                # Flush whatever is still buffered. Doing this in `finally`
                # guarantees the tail of the reply gets spoken even if the
                # stream was interrupted by an exception.
                trailing = buffer.strip()
                if trailing:
                    _spawn_tts(trailing)
                await sentence_queue.put(None)  # sentinel

        # ----- TTS consumer: synthesize ahead while prior sentence plays -----
        _SENTINEL = object()

        async def tts_consumer() -> None:
            pcm_bridge: asyncio.Queue[object] = asyncio.Queue(maxsize=256)
            announced_sr: Optional[int] = None

            async def pcm_producer() -> None:
                while True:
                    sentence = await sentence_queue.get()
                    if sentence is None:
                        await pcm_bridge.put(_SENTINEL)
                        return
                    got_audio = False
                    try:
                        async for pcm, sr in tts_service.stream_audio(
                            sentence, reply_lang, voice_gender
                        ):
                            if pcm:
                                got_audio = True
                                await pcm_bridge.put((pcm, sr))
                    except Exception as e:  # noqa: BLE001
                        logger.exception(
                            "TTS synth failed (engine=%s, lang=%s): %s",
                            engine,
                            reply_lang,
                            e,
                        )
                    if not got_audio:
                        logger.warning(
                            "TTS returned no audio for %r — browser fallback",
                            sentence[:60],
                        )
                        await self.send_json(
                            {
                                "type": "tts_text",
                                "text": sentence,
                                "language": reply_lang,
                            }
                        )

            async def pcm_sender() -> None:
                nonlocal announced_sr
                while True:
                    item = await pcm_bridge.get()
                    if item is _SENTINEL:
                        break
                    pcm, sr = item  # type: ignore[misc]
                    if announced_sr is None:
                        announced_sr = sr
                    elif sr != announced_sr:
                        await self.send_json(
                            {
                                "type": "tts_sample_rate",
                                "sample_rate": sr,
                            }
                        )
                        announced_sr = sr
                    await self.send_binary(pcm)

            producer_task = asyncio.create_task(pcm_producer())
            sender_task = asyncio.create_task(pcm_sender())
            try:
                await asyncio.gather(producer_task, sender_task)
            except Exception as e:  # noqa: BLE001
                producer_task.cancel()
                sender_task.cancel()
                raise e
            if tts_announced:
                await self.send_json({"type": "tts_end"})
            # Do NOT send status=idle here — the client re-opens the mic
            # only after its local playback queue drains.

        turn_start = time.perf_counter()
        producer_task = asyncio.create_task(llm_producer())
        consumer_task = asyncio.create_task(tts_consumer())

        try:
            await asyncio.gather(producer_task, consumer_task)
        except Exception as e:  # noqa: BLE001
            logger.exception("Turn execution failed: %s", e)
            await self.send_json(
                {"type": "error", "message": "I had trouble responding."}
            )
        finally:
            elapsed_ms = (time.perf_counter() - turn_start) * 1000.0
            full_reply = "".join(full_reply_parts).strip()
            if full_reply:
                self.history.append({"role": "user", "content": transcript})
                self.history.append(
                    {"role": "assistant", "content": full_reply}
                )
                if len(self.history) > 20:
                    self.history = self.history[-20:]
            logger.info(
                "Turn complete in %.0fms (lang=%s, engine=%s) — reply: %s",
                elapsed_ms,
                reply_lang,
                engine,
                full_reply[:80],
            )
            if not tts_announced:
                await self.send_json({"type": "status", "status": "idle"})

    # ---------- STT lifecycle ----------

    async def ensure_stt(self) -> None:
        """Create the Sarvam STT backend for the current language."""
        if self.stt is None:
            self.stt = await stt_service.start_session(
                self._on_transcript, language=self.language
            )

    async def reset_stt(self) -> None:
        if self.stt is not None:
            try:
                await self.stt.close()
            except Exception:  # noqa: BLE001
                pass
            self.stt = None
        await self.ensure_stt()

    async def feed_audio(self, pcm: bytes) -> None:
        """Buffer PCM for Sarvam STT."""
        if self.stt is not None:
            await self.stt.send_audio(pcm)

    async def finalize_utterance(self) -> None:
        """Called when VAD reports speech ended."""
        if self.stt is None:
            await self._emit_no_speech("no_stt")
            return

        loop = asyncio.get_running_loop()
        self._transcript_waiter = loop.create_future()
        self._got_transcript_this_turn = False
        await self.stt.finalize()
        no_speech_reason: Optional[str] = None
        try:
            await asyncio.wait_for(self._transcript_waiter, timeout=2.5)
        except asyncio.TimeoutError:
            no_speech_reason = "timeout"
        finally:
            self._transcript_waiter = None
            if not self._got_transcript_this_turn:
                await self._emit_no_speech(no_speech_reason or "empty")

    async def set_language(self, language: str) -> None:
        if language not in SUPPORTED_LANGUAGES:
            await self.send_json(
                {"type": "error", "message": f"Unsupported language: {language}"}
            )
            return
        if language == self.language:
            return
        logger.info(
            "Switching language: %s -> %s", self.language, language
        )
        self.language = language
        await self.reset_stt()
        await self.send_json(
            {"type": "language_set", "language": language}
        )

    async def set_voice_gender(
        self, gender: str, *, notify: bool = True
    ) -> None:
        gender = (gender or "").lower()
        if gender not in ("male", "female"):
            return
        changed = gender != self.voice_gender
        self.voice_gender = gender
        if changed:
            logger.info("Voice gender -> %s", gender)
        if not notify and not changed:
            return
        uc = get_use_case(self.use_case_id)
        await self.send_json(
            {
                "type": "voice_gender_set",
                "voice_gender": gender,
                **tts_voice_metadata(gender, "sarvam"),
                "persona_name": (
                    uc.persona_name_female
                    if gender == "female"
                    else uc.persona_name_male
                ),
            }
        )

    async def set_use_case(self, use_case_id: str) -> None:
        """Switch the active demo agent. Resets per-use-case session slots."""
        if not use_case_id:
            return
        new_uc = get_use_case(use_case_id)
        changed = new_uc.id != self.use_case_id
        if changed:
            agent_llm.clear_session(self.session_id, self.use_case_id)
            self.use_case_id = new_uc.id
            self.history.clear()
            logger.info("Use case -> %s (%s)", new_uc.id, new_uc.name)
        default_gender = new_uc.default_voice_gender or "female"
        await self.set_voice_gender(default_gender, notify=True)
        await self.send_json(
            {
                "type": "use_case_set",
                "use_case_id": new_uc.id,
                "use_case": new_uc.to_metadata(),
            }
        )

    async def run_text_turn(self, text: str) -> None:
        """Chat-only turn (no STT/TTS) — streams LLM tokens then sends `text_done`."""
        text = (text or "").strip()
        if not text:
            return
        await self.send_json({"type": "transcript", "text": text})
        await self.send_json({"type": "status", "status": "thinking"})

        reply_lang = self._resolve_reply_language(None)
        full_parts: list[str] = []
        try:
            async for token in llm_service.stream_response(
                text,
                self.history,
                language=reply_lang,
                voice_gender=self.voice_gender,
                session_id=self.session_id,
                use_case_id=self.use_case_id,
            ):
                if not token:
                    continue
                full_parts.append(token)
                await self.send_json({"type": "llm_token", "text": token})
        except Exception as e:  # noqa: BLE001
            logger.exception("Text turn failed: %s", e)
            await self.send_json(
                {"type": "error", "message": "I had trouble responding."}
            )

        full_reply = "".join(full_parts).strip()
        if full_reply:
            self.history.append({"role": "user", "content": text})
            self.history.append({"role": "assistant", "content": full_reply})
            if len(self.history) > 20:
                self.history = self.history[-20:]

        await self.send_json(
            {"type": "text_done", "reply": full_reply, "language": reply_lang}
        )
        await self.send_json({"type": "status", "status": "idle"})

    async def end_session_and_report(self) -> None:
        """Build entity report and send to client when call ends."""
        report = await agent_llm.build_session_report(
            self.history, self.session_id, use_case_id=self.use_case_id
        )
        await self.send_json({"type": "session_report", "report": report})
        agent_llm.clear_session(self.session_id, self.use_case_id)

    async def start(self) -> None:
        await self.ensure_stt()
        self.worker_task = asyncio.create_task(self._worker_loop())

    async def close(self) -> None:
        if not self._closed and self.history:
            try:
                report = await agent_llm.build_session_report(
                    self.history, self.session_id, use_case_id=self.use_case_id
                )
                await self.send_json(
                    {"type": "session_report", "report": report}
                )
            except Exception as e:  # noqa: BLE001
                logger.debug("Session report on close failed: %s", e)
            agent_llm.clear_session(self.session_id, self.use_case_id)
        self._closed = True
        if self.worker_task is not None:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except (asyncio.CancelledError, Exception):  # noqa: BLE001
                pass
        if self.stt is not None:
            try:
                await self.stt.close()
            except Exception:  # noqa: BLE001
                pass
            self.stt = None


async def _safe_close(websocket: WebSocket) -> None:
    try:
        await websocket.close()
    except RuntimeError:
        pass
    except Exception as e:  # noqa: BLE001
        logger.debug("websocket.close raised: %s", e)


@router.websocket("/ws/voice")
async def voice_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    session = VoiceSession(websocket)

    try:
        await session.start()
        active_uc = get_use_case(session.use_case_id)
        await session.send_json(
            {
                "type": "ready",
                "language": session.language,
                "supported_languages": list(SUPPORTED_LANGUAGES),
                "use_case_id": active_uc.id,
                "use_case": active_uc.to_metadata(),
                "use_cases": list_use_cases(),
                # Backward-compat fields for the existing UI.
                "college_id": active_uc.id,
                "college_name": f"{active_uc.name} — {active_uc.company}",
            }
        )
    except Exception as e:  # noqa: BLE001
        logger.exception("Failed to start voice session: %s", e)
        await session.send_json(
            {"type": "error", "message": f"Failed to start session: {e}"}
        )
        await session.close()
        await _safe_close(websocket)
        return

    try:
        while True:
            message = await websocket.receive()

            if message.get("type") == "websocket.disconnect":
                break

            if "bytes" in message and message["bytes"] is not None:
                pcm = message["bytes"]
                await session.feed_audio(pcm)
                continue

            text = message.get("text")
            if text is None:
                continue
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON from client: %s", text[:200])
                continue

            msg_type = payload.get("type")
            if msg_type == "speech_end":
                await session.finalize_utterance()
            elif msg_type == "clear_history":
                session.history.clear()
                college_llm.clear_session(session.session_id)
                await session.send_json({"type": "history_cleared"})
            elif msg_type == "ping":
                await session.send_json({"type": "pong"})
            elif msg_type == "interrupt":
                while not session.transcript_queue.empty():
                    try:
                        session.transcript_queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break
            elif msg_type == "set_language":
                await session.set_language(payload.get("language", "auto"))
            elif msg_type == "set_voice_gender":
                await session.set_voice_gender(
                    payload.get("voice_gender", "female")
                )
            elif msg_type == "set_user_gender":
                await session.set_voice_gender(
                    payload.get("user_gender", "female")
                )
            elif msg_type == "set_use_case":
                await session.set_use_case(payload.get("use_case_id", ""))
            elif msg_type == "text_message":
                await session.run_text_turn(payload.get("text", ""))
            elif msg_type == "end_session":
                await session.end_session_and_report()
            else:
                logger.debug("Unknown message type: %s", msg_type)

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:  # noqa: BLE001
        logger.exception("WebSocket error: %s", e)
    finally:
        session._closed = True
        await session.close()
        await _safe_close(websocket)
