from pathlib import Path
from typing import Optional, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parent / ".env"


# ---- Language config -------------------------------------------------------
SUPPORTED_LANGUAGES = ("auto", "en", "hi", "gu")

# Sarvam Saaras v3 STT language codes per UI selection.
# `auto` uses `unknown` so Sarvam auto-detects English, Hindi, and Gujarati.
SARVAM_STT_LANGUAGE_MAP = {
    "auto": "unknown",
    "en": "en-IN",
    "hi": "hi-IN",
    "gu": "gu-IN",
}

# Human-readable language names used in LLM system prompts.
LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi (हिन्दी)",
    "gu": "Gujarati (ગુજરાતી)",
    "auto": "auto-detected English/Hindi/Gujarati",
}


def normalize_detected_language(code: Optional[str]) -> Optional[str]:
    """Map Sarvam BCP-47 codes (hi-IN, gu-IN, en-IN) to UI codes."""
    if not code:
        return None
    d = code.lower()
    if d.startswith("hi"):
        return "hi"
    if d.startswith("gu"):
        return "gu"
    if d.startswith("en"):
        return "en"
    return None

# Which language uses which backend TTS engine. Sarvam Bulbul handles English
# (Indian accent), Hindi, and Gujarati, so all app speech uses one TTS stack.
TTS_ENGINE_FOR = {
    "en": "sarvam",
    "hi": "sarvam",
    "gu": "sarvam",
    "auto": "sarvam",  # resolved per-turn at runtime
}

# Sarvam language codes per UI language.
SARVAM_LANGUAGE_CODE = {
    "hi": "hi-IN",
    "gu": "gu-IN",
    "en": "en-IN",
}


# ---- Bot voice (frontend selects male or female TTS voice) -----------------
# bulbul:v3 speakers — priya is female-only on v3 (not available on v2).
SARVAM_VOICES = {
    "female": "priya",
    "male": "rahul",
}


def sarvam_voice_for(voice_gender: str) -> str:
    """Map UI voice gender to Sarvam bulbul:v3 speaker id."""
    return SARVAM_VOICES.get(
        (voice_gender or "").lower(), SARVAM_VOICES["female"]
    )


def tts_voice_metadata(
    voice_gender: str,
    engine: str = "sarvam",
) -> dict[str, str]:
    """Canonical TTS labels for WebSocket + UI (matches Sarvam speaker ids)."""
    if engine == "browser":
        return {
            "tts_engine": "browser",
            "tts_speaker": "",
            "tts_model": "",
            "tts_voice_label": "Browser speech (OS voice)",
        }
    speaker = sarvam_voice_for(voice_gender)
    model = settings.sarvam_model
    display_name = speaker.capitalize()
    return {
        "tts_engine": "sarvam",
        "tts_speaker": speaker,
        "tts_model": model,
        "tts_voice_label": f"Sarvam · {display_name} · {model}",
    }


def assistant_persona_instruction(
    voice_gender: str,
    language: str,
    agent_female: str = "Priya",
    agent_male: str = "Rahul",
    role: str = "LDCE college helpdesk assistant",
) -> str:
    """LLM persona: feminine/masculine grammar + first-person voice assistant.

    The use-case-aware nodes pass the demo's agent name + role; legacy
    callers without those args default to the LDCE persona for backward
    compatibility.
    """
    g = (voice_gender or "female").lower()
    lang = (language or "en").lower()
    name = agent_female if g == "female" else agent_male

    if g == "female":
        if lang == "hi":
            return (
                f"You are {name}, a female {role} speaking over voice. ALWAYS "
                "use feminine Hindi grammar for yourself: करती हूँ, बताती हूँ, "
                "मदद करती हूँ, समझती हूँ — never masculine forms like करता "
                "हूँ or बताता हूँ. Refer to yourself as female (मैं...). Warm, "
                "professional, helpful tone."
            )
        if lang == "gu":
            return (
                f"You are {name}, a female {role} speaking over voice. ALWAYS "
                "use feminine Gujarati grammar for yourself: કરું છું, કહું "
                "છું, મદદ કરું છું — refer to yourself as female. Warm, "
                "professional tone."
            )
        return (
            f"You are {name}, a female {role}. "
            "Use natural feminine first-person phrasing. Warm, professional tone."
        )

    # male
    if lang == "hi":
        return (
            f"You are {name}, a male {role} speaking over voice. ALWAYS use "
            "masculine Hindi grammar for yourself: करता हूँ, बताता हूँ, मदद "
            "करता हूँ — never feminine forms. Warm, professional."
        )
    if lang == "gu":
        return (
            f"You are {name}, a male {role} speaking over voice. ALWAYS use "
            "masculine Gujarati grammar for yourself. Warm, professional tone."
        )
    return (
        f"You are {name}, a male {role}. "
        "Use natural masculine first-person phrasing. Warm, professional tone."
    )


def voice_speech_style_instruction(language: str) -> str:
    """
    Instructions for speakable TTS output: natural human speech with
    English kept in Latin script for proper nouns / technical terms when
    replying in Hindi or Gujarati (Indian code-mixing).
    """
    lang = (language or "en").lower()
    if lang.startswith("hi"):
        lang = "hi"
    elif lang.startswith("gu"):
        lang = "gu"
    elif lang.startswith("en"):
        lang = "en"

    english_keep = (
        "KEEP IN ENGLISH (Latin/Roman letters only — do NOT write these in "
        "Devanagari or Gujarati script):\n"
        "• College/institution: LDCE, L.D. College of Engineering, GTU, Gujarat Technological University\n"
        "• Branches & courses: Computer Engineering, Information Technology, "
        "Mechanical Engineering, Civil Engineering, Electrical Engineering, "
        "Electronics and Communication, Artificial Intelligence and Machine Learning, MCA, MBA, etc.\n"
        "• Common campus terms: admission, placement, hostel, campus, semester, "
        "internship, scholarship, fees, counselling, eligibility, cutoff\n"
        "• Degrees & levels: UG, PG, BTech, MTech, B.E., M.E.\n"
        "• Processes & bodies: ACPC, GTU PGCET, SSIP, DTE\n"
        "• Recruiter/company names: IBM, TCS, Infosys, Accenture, etc.\n"
        "• Web & contact: ldce.ac.in, email addresses, phone numbers\n"
        "• Any proper noun, acronym, brand, or technical term that sounds "
        "unnatural or mispronounced when transliterated to Hindi/Gujarati script"
    )

    voice_basics = (
        "VOICE RULES (output will be read aloud by TTS):\n"
        "• Sound like a real human on a phone call — warm, clear, conversational\n"
        "• 1-3 short sentences only; no markdown, bullets, lists, or symbols\n"
        "• Avoid formal written language; use spoken phrasing\n"
        "• Do not spell out URLs letter-by-letter; say ldce.ac.in naturally"
    )

    if lang == "en":
        return (
            f"{voice_basics}\n"
            "• Reply fully in natural Indian English\n"
            "• Use contractions where natural (I'm, you'll, it's)\n"
            "• Keep all proper nouns in standard English spelling"
        )

    if lang == "hi":
        return (
            f"{voice_basics}\n"
            "• Reply in natural spoken Hinglish — Hindi (Devanagari) sentence "
            "structure with English mixed in where real students/counsellors "
            "in Ahmedabad actually use English words\n"
            f"{english_keep}\n"
            "• Example style: \"LDCE में Computer Engineering की admission "
            "ACPC counselling से होती है। exact dates के लिए ldce.ac.in "
            "check कर सकते हैं।\"\n"
            "• WRONG: transliterating Computer Engineering as कम्प्यूटर "
            "इंजीनियरिंग or LDCE as एलडीसी — always keep the English form"
        )

    if lang == "gu":
        return (
            f"{voice_basics}\n"
            "• Reply in natural spoken Guenglish — Gujarati (Gujarati script) "
            "sentence structure with English mixed in where Gujarati speakers "
            "naturally use English on campus\n"
            f"{english_keep}\n"
            "• Example style: \"LDCE ma Computer Engineering ma admission "
            "ACPC counselling thi thay che. exact dates mate ldce.ac.in "
            "check kari shakay.\"\n"
            "• WRONG: writing Computer Engineering or LDCE in Gujarati script — "
            "keep the English spelling"
        )

    # auto — mirror user's language; apply code-mix rules for hi/gu
    return (
        f"{voice_basics}\n"
        "• Match the language the user spoke (English, Hindi, or Gujarati)\n"
        "• If replying in Hindi or Gujarati, use natural code-mixed speech:\n"
        f"{english_keep}\n"
        "• If the user already used English for a term (e.g. \"Computer Engineering fees\"), "
        "keep that term in English in your reply too"
    )


def llm_response_language_instruction(language: str) -> str:
    """Combined language + speakable voice style for agent prompts."""
    lang = (language or "en").lower()
    if lang.startswith("hi"):
        base = "Hindi (Devanagari) with natural Hinglish code-mixing"
    elif lang.startswith("gu"):
        base = "Gujarati script with natural Guenglish code-mixing"
    elif lang.startswith("en"):
        base = "English"
    else:
        base = "same language the user used (English, Hindi, or Gujarati)"
    return f"{base}\n\n{voice_speech_style_instruction(language)}"


class Settings(BaseSettings):
    groq_api_key: str
    sarvam_api_key: str
    host: str = "0.0.0.0"
    port: int = 8000
    # Comma-separated origins (str avoids pydantic-settings JSON-parsing list fields)
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]

    # LLM
    llm_model: str = "llama-3.3-70b-versatile"

    # Sarvam STT (English / Hindi / Gujarati / auto)
    sarvam_stt_model: str = "saaras:v3"

    # Sarvam TTS — bulbul:v3 required for priya/rahul voices
    sarvam_model: str = "bulbul:v3"
    sarvam_speaker: str = "priya"
    sarvam_sample_rate: int = 24000
    sarvam_pace: float = 1.0
    sarvam_pitch: float = 0.0
    sarvam_loudness: float = 1.5

    # Default language if client never sends a selection.
    default_language: str = "auto"

    # College voicebot (knowledge in college/data/{college_id}.json)
    college_id: str = "ldce"

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE if _ENV_FILE.is_file() else None,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
