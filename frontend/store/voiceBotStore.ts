import { create } from "zustand";
import { SARVAM_TTS_MODEL, sarvamSpeakerId } from "@/lib/voiceDisplay";
import type {
  ChatMessage,
  ConnectionStatus,
  Language,
  SessionReport,
  VoiceGender,
  VoiceStatus,
} from "@/types";

interface VoiceBotState {
  status: VoiceStatus;
  connection: ConnectionStatus;
  userTranscript: string;
  botReply: string;
  conversationHistory: ChatMessage[];
  latencyMs: number | null;
  errorMessage: string | null;
  collegeName: string;

  language: Language;
  voiceGender: VoiceGender;
  ttsEngine: "sarvam" | "browser";
  ttsVoiceLabel: string;
  ttsSpeaker: string;
  ttsModel: string;
  sessionReport: SessionReport | null;

  speechEndAt: number | null;

  setStatus: (s: VoiceStatus) => void;
  setConnection: (c: ConnectionStatus) => void;
  setUserTranscript: (t: string) => void;
  appendBotToken: (t: string) => void;
  clearBotReply: () => void;
  addToHistory: (m: ChatMessage) => void;
  clearHistory: () => void;
  setLatency: (ms: number | null) => void;
  markSpeechEnd: () => void;
  setError: (msg: string | null) => void;
  resetTurn: () => void;
  setLanguage: (l: Language) => void;
  setVoiceGender: (g: VoiceGender) => void;
  setTtsEngine: (e: "sarvam" | "browser") => void;
  setTtsVoiceInfo: (info: {
    label: string;
    speaker?: string;
    model?: string;
    engine?: "sarvam" | "browser";
  }) => void;
  setCollegeName: (n: string) => void;
  setSessionReport: (r: SessionReport | null) => void;
}

export const useVoiceBotStore = create<VoiceBotState>((set) => ({
  status: "idle",
  connection: "disconnected",
  userTranscript: "",
  botReply: "",
  conversationHistory: [],
  latencyMs: null,
  errorMessage: null,
  collegeName: "LDCE",
  speechEndAt: null,
  language: "auto",
  voiceGender: "female",
  ttsEngine: "sarvam",
  ttsVoiceLabel: "Priya · Sarvam Priya · bulbul:v3",
  ttsSpeaker: "priya",
  ttsModel: "bulbul:v3",
  sessionReport: null,

  setStatus: (s) => set({ status: s }),
  setConnection: (c) => set({ connection: c }),
  setUserTranscript: (t) => set({ userTranscript: t }),
  appendBotToken: (t) => set((state) => ({ botReply: state.botReply + t })),
  clearBotReply: () => set({ botReply: "" }),
  addToHistory: (m) =>
    set((state) => ({
      conversationHistory: [...state.conversationHistory, m],
    })),
  clearHistory: () =>
    set({
      conversationHistory: [],
      userTranscript: "",
      botReply: "",
      latencyMs: null,
      sessionReport: null,
    }),
  setLatency: (ms) => set({ latencyMs: ms }),
  markSpeechEnd: () => set({ speechEndAt: performance.now() }),
  setError: (msg) => set({ errorMessage: msg }),
  resetTurn: () =>
    set({
      userTranscript: "",
      botReply: "",
      speechEndAt: null,
    }),
  setLanguage: (l) => set({ language: l }),
  setVoiceGender: (g) =>
    set({
      voiceGender: g,
      ttsSpeaker: sarvamSpeakerId(g),
      ttsModel: SARVAM_TTS_MODEL,
      ttsEngine: "sarvam",
    }),
  setTtsEngine: (e) => set({ ttsEngine: e }),
  setTtsVoiceInfo: (info) =>
    set({
      ttsVoiceLabel: info.label,
      ...(info.speaker != null ? { ttsSpeaker: info.speaker } : {}),
      ...(info.model != null ? { ttsModel: info.model } : {}),
      ...(info.engine != null ? { ttsEngine: info.engine } : {}),
    }),
  setCollegeName: (n) => set({ collegeName: n }),
  setSessionReport: (r) => set({ sessionReport: r }),
}));
