from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field


Language = Literal["auto", "en", "hi", "gu"]


# ---------- Client -> Server JSON messages ----------

class ClientSpeechEnd(BaseModel):
    type: Literal["speech_end"]


class ClientClearHistory(BaseModel):
    type: Literal["clear_history"]


class ClientPing(BaseModel):
    type: Literal["ping"]


class ClientSetLanguage(BaseModel):
    type: Literal["set_language"]
    language: Language


class ClientSetUserGender(BaseModel):
    """Tells the backend which gender the *user* is. The bot persona is the
    opposite-sex romantic partner (boyfriend if user_gender=female,
    girlfriend if user_gender=male)."""
    type: Literal["set_user_gender"]
    user_gender: Literal["female", "male"]


# ---------- Server -> Client JSON messages ----------

class ServerTranscript(BaseModel):
    type: Literal["transcript"] = "transcript"
    text: str
    language: Optional[str] = None  # detected language if known


class ServerLLMToken(BaseModel):
    type: Literal["llm_token"] = "llm_token"
    text: str


class ServerTTSStart(BaseModel):
    type: Literal["tts_start"] = "tts_start"
    sentence: Optional[str] = None
    # "sarvam" → binary PCM follows; "browser" → emergency Web Speech fallback
    engine: Literal["sarvam", "browser"] = "sarvam"
    language: Optional[str] = None


class ServerTTSText(BaseModel):
    """Sent when the response is to be spoken by the browser (multilingual)."""
    type: Literal["tts_text"] = "tts_text"
    text: str
    language: str


class ServerTTSEnd(BaseModel):
    type: Literal["tts_end"] = "tts_end"


class ServerError(BaseModel):
    type: Literal["error"] = "error"
    message: str


class ServerStatus(BaseModel):
    type: Literal["status"] = "status"
    status: Literal["idle", "listening", "thinking", "speaking"]


class ServerPong(BaseModel):
    type: Literal["pong"] = "pong"


# ---------- Internal data structures ----------

class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(default="")
