export type VoiceStatus = "idle" | "listening" | "thinking" | "speaking";

export type ConnectionStatus =
  | "disconnected"
  | "connecting"
  | "connected"
  | "reconnecting"
  | "error";

export type Language = "auto" | "en" | "hi" | "gu";

/** Bot TTS voice — male or female assistant voice. */
export type VoiceGender = "female" | "male";

export interface VoiceGenderOption {
  code: VoiceGender;
  label: string;
}

export const VOICE_GENDER_OPTIONS: VoiceGenderOption[] = [
  { code: "female", label: "Priya · bulbul:v3" },
  { code: "male", label: "Rahul · bulbul:v3" },
];

/** @deprecated use VoiceGender */
export type UserGender = VoiceGender;

export interface LanguageOption {
  code: Language;
  label: string;
  native: string;
  flag: string;
}

export const LANGUAGE_OPTIONS: LanguageOption[] = [
  {
    code: "auto",
    label: "Auto-detect",
    native: "Auto EN/HI/GU",
    flag: "🌐",
  },
  { code: "en", label: "English", native: "English", flag: "🇬🇧" },
  { code: "hi", label: "Hindi", native: "हिन्दी", flag: "🇮🇳" },
  { code: "gu", label: "Gujarati", native: "ગુજરાતી", flag: "🇮🇳" },
];

export const SPEECH_LOCALE: Record<Language, string> = {
  auto: "en-US",
  en: "en-US",
  hi: "hi-IN",
  gu: "gu-IN",
};

export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface ExtractedEntity {
  type: string;
  value: string;
  confidence?: number;
}

export interface SessionReport {
  college_id?: string;
  college_name?: string;
  use_case_id?: string;
  use_case_name?: string;
  company?: string;
  conversation: ChatMessage[];
  slots: Record<string, unknown>;
  entities: ExtractedEntity[];
  summary: string;
  primary_intent: string;
  turn_count: number;
}

// ---------- WebSocket message protocol ----------

export type ClientControlMessage =
  | { type: "speech_end" }
  | { type: "clear_history" }
  | { type: "ping" }
  | { type: "interrupt" }
  | { type: "end_session" }
  | { type: "set_language"; language: Language }
  | { type: "set_voice_gender"; voice_gender: VoiceGender }
  | { type: "set_use_case"; use_case_id: string }
  | { type: "text_message"; text: string };

export type ServerMessage =
  | {
      type: "ready";
      language?: Language;
      supported_languages?: Language[];
      college_id?: string;
      college_name?: string;
      use_case_id?: string;
      use_case?: import("./useCase").UseCaseMetadata;
      use_cases?: import("./useCase").UseCaseMetadata[];
    }
  | { type: "transcript"; text: string; language?: string | null }
  | { type: "llm_token"; text: string }
  | {
      type: "tts_start";
      sentence?: string;
      engine?: "sarvam" | "browser";
      language?: Language;
      sample_rate?: number;
      voice_gender?: VoiceGender;
      tts_speaker?: string;
      tts_model?: string;
      tts_voice_label?: string;
    }
  | { type: "tts_sample_rate"; sample_rate: number }
  | { type: "tts_text"; text: string; language: Language }
  | { type: "tts_end" }
  | { type: "tts_chunk_start"; sentence?: string }
  | { type: "error"; message: string }
  | { type: "no_speech"; reason?: string; message?: string; language?: Language }
  | { type: "status"; status: VoiceStatus }
  | { type: "pong" }
  | { type: "history_cleared" }
  | { type: "language_set"; language: Language }
  | {
      type: "voice_gender_set";
      voice_gender: VoiceGender;
      tts_speaker?: string;
      tts_model?: string;
      tts_voice_label?: string;
      persona_name?: string;
    }
  | {
      type: "use_case_set";
      use_case_id: string;
      use_case: import("./useCase").UseCaseMetadata;
    }
  | { type: "session_report"; report: SessionReport }
  | { type: "text_done"; reply: string; language: Language };
