"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Mic, MicOff, Radio, RotateCcw, Volume2 } from "lucide-react";
import { toast } from "sonner";

import { AudioVisualizer } from "@/components/AudioVisualizer";
import { LanguageSelector } from "@/components/LanguageSelector";
import { StatusIndicator } from "@/components/StatusIndicator";
import { TranscriptPanel } from "@/components/TranscriptPanel";
import { VoiceGenderSelector } from "@/components/VoiceGenderSelector";
import { SessionReportPanel } from "@/components/SessionReportPanel";
import { useAudioCapture } from "@/hooks/useAudioCapture";
import { useAudioPlayback } from "@/hooks/useAudioPlayback";
import { useBrowserTTS } from "@/hooks/useBrowserTTS";
import { useVAD } from "@/hooks/useVAD";
import { useWebSocket } from "@/hooks/useWebSocket";
import { cn } from "@/lib/utils";
import { AUTO_LISTEN_ENABLED, SPEECH_END_FLUSH_MS } from "@/lib/voiceConfig";
import {
  SARVAM_TTS_MODEL,
  assistantVoiceLabel,
  browserVoiceLabel,
  sarvamSpeakerId,
} from "@/lib/voiceDisplay";
import { accentStyles } from "@/lib/useCases";
import { useVoiceBotStore } from "@/store/voiceBotStore";
import type { Language, ServerMessage, VoiceGender } from "@/types";
import type { UseCaseMetadata } from "@/types/useCase";

const WS_URL =
  process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws/voice";

interface VoiceBotProps {
  /** Use-case id to attach to (e.g. "real_estate"). */
  useCaseId?: string;
  /** Domain accent for themed voice UI (emerald, amber, …). */
  accent?: string;
  /** Header title — defaults to store collegeName from server. */
  title?: string;
  /** Footer subtitle line. */
  subtitle?: string;
  /** Per-demo default TTS gender from use-case config. */
  defaultVoiceGender?: VoiceGender;
  personaNameFemale?: string;
  personaNameMale?: string;
}

export function VoiceBot({
  useCaseId,
  accent = "teal",
  title,
  subtitle,
  defaultVoiceGender = "female",
  personaNameFemale = "Priya",
  personaNameMale = "Rahul",
}: VoiceBotProps = {}) {
  const theme = accentStyles(accent).voice;
  const status = useVoiceBotStore((s) => s.status);
  const connection = useVoiceBotStore((s) => s.connection);
  const userTranscript = useVoiceBotStore((s) => s.userTranscript);
  const botReply = useVoiceBotStore((s) => s.botReply);
  const latencyMs = useVoiceBotStore((s) => s.latencyMs);
  const errorMessage = useVoiceBotStore((s) => s.errorMessage);
  const language = useVoiceBotStore((s) => s.language);
  const voiceGender = useVoiceBotStore((s) => s.voiceGender);
  const collegeName = useVoiceBotStore((s) => s.collegeName);
  const sessionReport = useVoiceBotStore((s) => s.sessionReport);
  const ttsEngine = useVoiceBotStore((s) => s.ttsEngine);
  const ttsVoiceLabel = useVoiceBotStore((s) => s.ttsVoiceLabel);
  const ttsSpeaker = useVoiceBotStore((s) => s.ttsSpeaker);
  const ttsModel = useVoiceBotStore((s) => s.ttsModel);

  const {
    setStatus,
    setConnection,
    setUserTranscript,
    appendBotToken,
    clearBotReply,
    addToHistory,
    clearHistory,
    setLatency,
    markSpeechEnd,
    setError,
    setLanguage,
    setVoiceGender,
    setTtsEngine,
    setTtsVoiceInfo,
    setCollegeName,
    setSessionReport,
  } = useVoiceBotStore();

  const [enabled, setEnabled] = useState(false);
  // True after server sends tts_end; mic re-opens only when playback drains.
  const awaitingPlaybackEndRef = useRef(false);
  // Delay flipping to "thinking" so trailing mic audio can reach the server.
  const speechFlushTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const thinkingWatchdogRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  // True once binary PCM TTS audio arrives for the current utterance.
  const pcmAudioReceivedRef = useRef(false);
  // True when server fell back to browser speechSynthesis (tts_text).
  const browserTtsUsedRef = useRef(false);
  const playbackEndWatchdogRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pauseListeningRef = useRef<() => void>(() => {});
  const resumeListeningRef = useRef<() => void>(() => {});
  const vadStartRef = useRef<() => void>(() => {});
  /** Synchronous mic gate — blocks PCM before React status re-renders. */
  const micGateOpenRef = useRef(false);
  const [micGateOpen, setMicGateOpenState] = useState(false);

  const setMicGate = useCallback((open: boolean) => {
    micGateOpenRef.current = open;
    setMicGateOpenState(open);
  }, []);

  // ---------------- Half-duplex listening ----------------
  // Mic + VAD are gated off the instant TTS/thinking starts (micGate + VAD pause).
  // They reopen only after playback ends, or when AUTO_LISTEN is on and bot is idle.
  // Set NEXT_PUBLIC_AUTO_LISTEN=true in .env.local for continuous auto-listen.

  // ---------------- Browser TTS (Hindi / Gujarati) ----------------
  const browserTTS = useBrowserTTS({
    voiceGender,
    onStart: () => {
      pauseListeningRef.current();
      setStatus("speaking");
    },
    onEnd: () => {
      if (!awaitingPlaybackEndRef.current) return;
      awaitingPlaybackEndRef.current = false;
      if (playbackEndWatchdogRef.current) {
        clearTimeout(playbackEndWatchdogRef.current);
        playbackEndWatchdogRef.current = null;
      }
      resumeListeningRef.current();
    },
  });

  // ---------------- Streaming PCM playback (Aura + Sarvam) ----------------
  const {
    enqueueAudio,
    stopPlayback,
    setSampleRate,
    resetStream,
    markStreamComplete,
    analyser: playbackAnalyser,
    unlock: unlockPlayback,
  } = useAudioPlayback({
    sampleRate: 24000,
    onPlaybackStart: () => {
      pauseListeningRef.current();
      setStatus("speaking");
    },
    onPlaybackEnd: () => {
      // Ignore spurious end events — only resume after server tts_end + drain.
      if (!awaitingPlaybackEndRef.current) return;
      awaitingPlaybackEndRef.current = false;
      if (playbackEndWatchdogRef.current) {
        clearTimeout(playbackEndWatchdogRef.current);
        playbackEndWatchdogRef.current = null;
      }
      resumeListeningRef.current();
    },
  });

  // ---------------- WebSocket ----------------
  const syncVoiceLabel = useCallback(
    (gender: VoiceGender, personaOverride?: string) => {
      const label = personaOverride
        ? `${personaOverride} · Sarvam ${sarvamSpeakerId(gender)} · ${SARVAM_TTS_MODEL}`
        : assistantVoiceLabel(gender, personaNameFemale, personaNameMale);
      setTtsVoiceInfo({
        label,
        speaker: sarvamSpeakerId(gender),
        model: SARVAM_TTS_MODEL,
        engine: "sarvam",
      });
    },
    [personaNameFemale, personaNameMale, setTtsVoiceInfo],
  );

  const applyUseCaseVoice = useCallback(
    (uc: Pick<
      UseCaseMetadata,
      "default_voice_gender" | "persona_name_female" | "persona_name_male"
    >) => {
      const g = uc.default_voice_gender ?? "female";
      setVoiceGender(g);
      setTtsVoiceInfo({
        label: assistantVoiceLabel(
          g,
          uc.persona_name_female,
          uc.persona_name_male,
        ),
        speaker: sarvamSpeakerId(g),
        model: SARVAM_TTS_MODEL,
        engine: "sarvam",
      });
    },
    [setTtsVoiceInfo, setVoiceGender],
  );

  useEffect(() => {
    setVoiceGender(defaultVoiceGender);
    syncVoiceLabel(defaultVoiceGender);
  }, [
    defaultVoiceGender,
    personaNameFemale,
    personaNameMale,
    setVoiceGender,
    syncVoiceLabel,
  ]);

  const handleServerMessage = useCallback(
    (msg: ServerMessage) => {
      switch (msg.type) {
        case "ready":
          setError(null);
          if (msg.college_name) setCollegeName(msg.college_name);
          if (msg.use_case) {
            applyUseCaseVoice(msg.use_case);
          }
          break;
        case "use_case_set":
          applyUseCaseVoice(msg.use_case);
          break;
        case "session_report":
          setSessionReport(msg.report);
          break;
        case "voice_gender_set": {
          const g = msg.voice_gender ?? voiceGender;
          setVoiceGender(g);
          if (msg.persona_name) {
            syncVoiceLabel(g, msg.persona_name);
          } else if (msg.tts_voice_label) {
            setTtsVoiceInfo({
              label: msg.tts_voice_label,
              speaker: msg.tts_speaker,
              model: msg.tts_model,
              engine: "sarvam",
            });
          } else {
            syncVoiceLabel(g);
          }
          break;
        }
        case "transcript": {
          if (speechFlushTimerRef.current) {
            clearTimeout(speechFlushTimerRef.current);
            speechFlushTimerRef.current = null;
          }
          if (thinkingWatchdogRef.current) {
            clearTimeout(thinkingWatchdogRef.current);
            thinkingWatchdogRef.current = null;
          }
          setUserTranscript(msg.text);
          addToHistory({ role: "user", content: msg.text });
          clearBotReply();
          break;
        }
        case "llm_token":
          appendBotToken(msg.text);
          break;
        case "tts_start": {
          if (thinkingWatchdogRef.current) {
            clearTimeout(thinkingWatchdogRef.current);
            thinkingWatchdogRef.current = null;
          }
          pcmAudioReceivedRef.current = false;
          browserTtsUsedRef.current = false;
          awaitingPlaybackEndRef.current = false;
          if (playbackEndWatchdogRef.current) {
            clearTimeout(playbackEndWatchdogRef.current);
            playbackEndWatchdogRef.current = null;
          }
          const engine = (msg.engine || "sarvam") as
            | "sarvam"
            | "browser";
          setTtsEngine(engine);
          if (msg.tts_voice_label) {
            setTtsVoiceInfo({
              label: msg.tts_voice_label,
              speaker: msg.tts_speaker,
              model: msg.tts_model,
              engine,
            });
          }
          if (msg.voice_gender) {
            setVoiceGender(msg.voice_gender);
          }
          resetStream();
          stopPlayback();
          browserTTS.cancel();
          if (msg.sample_rate) {
            setSampleRate(msg.sample_rate);
          } else {
            setSampleRate(engine === "sarvam" ? 24000 : 24000);
          }
          // Half-duplex: mute mic + pause VAD while bot speaks.
          pauseListeningRef.current();
          setStatus("speaking");
          break;
        }
        case "tts_sample_rate": {
          if (msg.sample_rate) setSampleRate(msg.sample_rate);
          break;
        }
        case "tts_text": {
          browserTtsUsedRef.current = true;
          setTtsEngine("browser");
          setTtsVoiceInfo({
            label: "Browser speech (OS voice)",
            engine: "browser",
          });
          // Server-driven fallback: only used if a backend TTS fails and the
          // backend asks the browser to synthesise instead.
          if (browserTTS.isSupported) {
            browserTTS.speak(msg.text, msg.language);
          } else {
            toast.error(
              "Your browser doesn't support multilingual speech synthesis.",
            );
          }
          break;
        }
        case "tts_end": {
          const reply = useVoiceBotStore.getState().botReply;
          if (reply.trim()) {
            addToHistory({ role: "assistant", content: reply });
          }
          const usedBrowser = browserTtsUsedRef.current;
          const usedPcm = pcmAudioReceivedRef.current;
          if (usedBrowser) {
            awaitingPlaybackEndRef.current = true;
            browserTTS.flush();
          } else if (usedPcm) {
            // Server done sending — wait for local playback queue to drain.
            awaitingPlaybackEndRef.current = true;
            markStreamComplete();
          } else {
            // No audio at all — unblock after a short delay.
            window.setTimeout(() => {
              if (awaitingPlaybackEndRef.current) return;
              resumeListeningRef.current();
            }, 400);
          }
          // Safety net: never stay stuck in speaking forever.
          if (playbackEndWatchdogRef.current) {
            clearTimeout(playbackEndWatchdogRef.current);
          }
          playbackEndWatchdogRef.current = setTimeout(() => {
            playbackEndWatchdogRef.current = null;
            if (!awaitingPlaybackEndRef.current) return;
            awaitingPlaybackEndRef.current = false;
            resumeListeningRef.current();
          }, 45000);
          break;
        }
        case "error":
          setError(msg.message);
          awaitingPlaybackEndRef.current = false;
          if (thinkingWatchdogRef.current) {
            clearTimeout(thinkingWatchdogRef.current);
            thinkingWatchdogRef.current = null;
          }
          resumeListeningRef.current();
          toast.error(msg.message);
          break;
        case "no_speech":
          if (speechFlushTimerRef.current) {
            clearTimeout(speechFlushTimerRef.current);
            speechFlushTimerRef.current = null;
          }
          if (thinkingWatchdogRef.current) {
            clearTimeout(thinkingWatchdogRef.current);
            thinkingWatchdogRef.current = null;
          }
          setUserTranscript("");
          if (msg.message) {
            clearBotReply();
            appendBotToken(msg.message);
          } else {
            awaitingPlaybackEndRef.current = false;
            setStatus("idle");
            if (AUTO_LISTEN_ENABLED) {
              setMicGate(true);
              vadStartRef.current();
            } else {
              setMicGate(false);
            }
            toast.message("Didn't catch that — please try again");
          }
          break;
        case "status":
          if (msg.status === "thinking" || msg.status === "speaking") {
            pauseListeningRef.current();
          }
          // Ignore server idle while audio is still playing locally.
          if (
            msg.status === "idle" &&
            awaitingPlaybackEndRef.current
          ) {
            break;
          }
          setStatus(msg.status);
          break;
        case "history_cleared":
          toast.success("Conversation cleared");
          break;
        case "language_set":
          toast.success(`Language: ${msg.language}`);
          break;
        case "pong":
          break;
        default:
          break;
      }
    },
    [
      addToHistory,
      appendBotToken,
      browserTTS,
      clearBotReply,
      setCollegeName,
      setError,
      setSampleRate,
      setSessionReport,
      setStatus,
      setTtsEngine,
      setTtsVoiceInfo,
      applyUseCaseVoice,
      syncVoiceLabel,
      setVoiceGender,
      setUserTranscript,
      setMicGate,
      stopPlayback,
      resetStream,
      markStreamComplete,
    ],
  );

  const handleAudioChunk = useCallback(
    (data: ArrayBuffer) => {
      pcmAudioReceivedRef.current = true;
      const t0 = useVoiceBotStore.getState().speechEndAt;
      if (t0 != null && useVoiceBotStore.getState().latencyMs == null) {
        const lat = performance.now() - t0;
        setLatency(lat);
        console.log(`[LATENCY] STT→LLM→TTS: ${Math.round(lat)}ms`);
      }
      void unlockPlayback().then(() => {
        enqueueAudio(data);
      });
    },
    [enqueueAudio, setLatency, unlockPlayback],
  );

  const { sendAudio, sendJSON, connectionStatus } = useWebSocket({
    url: WS_URL,
    onAudioChunk: handleAudioChunk,
    onMessage: handleServerMessage,
    autoConnect: true,
  });

  useEffect(() => {
    setConnection(connectionStatus);
  }, [connectionStatus, setConnection]);

  // Push language + voice-gender to server whenever they change or the
  // connection reconnects.
  useEffect(() => {
    if (connectionStatus === "connected" && useCaseId) {
      sendJSON({ type: "set_use_case", use_case_id: useCaseId });
    }
  }, [connectionStatus, useCaseId, sendJSON]);

  useEffect(() => {
    if (connectionStatus === "connected") {
      sendJSON({ type: "set_language", language });
    }
  }, [connectionStatus, language, sendJSON]);

  // ---------------- Audio capture (mic -> WS) ----------------
  const onPcmChunk = useCallback(
    (pcm: ArrayBuffer) => {
      // Hard block — never send audio while bot speaks/thinks or gate is closed.
      if (!micGateOpenRef.current) return;
      const s = useVoiceBotStore.getState().status;
      if (s === "speaking" || s === "thinking") return;
      sendAudio(pcm);
    },
    [sendAudio],
  );

  // Mic streams only when session is on, gate is open, and bot is not busy.
  const canListen =
    enabled &&
    micGateOpen &&
    (status === "idle" || status === "listening");

  const { start: startCapture, stop: stopCapture, permissionError } =
    useAudioCapture({
      targetSampleRate: 16000,
      onPcmChunk,
      // Stop streaming PCM to the backend the instant the bot starts
      // thinking / speaking. The worklet stays alive — we just suppress
      // the postMessage path.
      enabled: canListen,
    });

  // ---------------- VAD ----------------
  // Half-duplex: we hard-pause the VAD worklet during thinking + speaking
  // (see effect below), so callbacks below should only fire when listening
  // is actually allowed. We still guard defensively in case of late events.
  const vad = useVAD({
    startOnLoad: false,
    onSpeechStart: () => {
      const cur = useVoiceBotStore.getState().status;
      if (cur === "speaking" || cur === "thinking") {
        return;
      }
      setStatus("listening");
    },
    onSpeechEnd: () => {
      const cur = useVoiceBotStore.getState().status;
      if (cur !== "listening") {
        return;
      }
      markSpeechEnd();
      setLatency(null);
      // Send speech_end immediately but keep status "listening" briefly so
      // the AudioWorklet can flush the last PCM frames to the server.
      sendJSON({ type: "speech_end" });
      if (speechFlushTimerRef.current) {
        clearTimeout(speechFlushTimerRef.current);
      }
      speechFlushTimerRef.current = setTimeout(() => {
        speechFlushTimerRef.current = null;
        if (useVoiceBotStore.getState().status !== "listening") {
          return;
        }
        pauseListeningRef.current();
        setStatus("thinking");
        // Safety net: never stay stuck in thinking forever.
        if (thinkingWatchdogRef.current) {
          clearTimeout(thinkingWatchdogRef.current);
        }
        thinkingWatchdogRef.current = setTimeout(() => {
          thinkingWatchdogRef.current = null;
          if (useVoiceBotStore.getState().status === "thinking") {
            resumeListeningRef.current();
            toast.error("Response timed out — please try again");
          }
        }, 12000);
      }, SPEECH_END_FLUSH_MS);
    },
    onVADMisfire: () => {
      const cur = useVoiceBotStore.getState().status;
      if (cur === "listening") {
        setStatus("idle");
      }
    },
  });
  const prewarmVAD = vad.prewarm;
  const vadPause = vad.pause;
  const vadStart = vad.start;

  /** Stop mic + VAD immediately — no audio sent, no speech detection. */
  const pauseListening = useCallback(() => {
    setMicGate(false);
    vadPause();
  }, [setMicGate, vadPause]);

  /** Re-open mic + VAD after bot finishes speaking (or on error timeout). */
  const resumeListening = useCallback(() => {
    if (!enabled) return;
    const s = useVoiceBotStore.getState().status;
    if (s !== "speaking" && s !== "thinking") return;
    setStatus("idle");
    setMicGate(true);
    void vadStart();
  }, [enabled, setMicGate, setStatus, vadStart]);

  /** Manual mode: user tapped mic to speak before any TTS has played. */
  const openMicForUserTurn = useCallback(() => {
    if (!enabled) return;
    const s = useVoiceBotStore.getState().status;
    if (s === "speaking" || s === "thinking") return;
    setStatus("idle");
    setMicGate(true);
    void vadStart();
  }, [enabled, setMicGate, setStatus, vadStart]);

  useEffect(() => {
    pauseListeningRef.current = pauseListening;
  }, [pauseListening]);
  useEffect(() => {
    resumeListeningRef.current = resumeListening;
  }, [resumeListening]);
  useEffect(() => {
    vadStartRef.current = () => {
      void vadStart();
    };
  }, [vadStart]);

  // Force gate closed + VAD paused whenever bot is thinking or speaking.
  useEffect(() => {
    if (!enabled) return;
    if (status === "speaking" || status === "thinking") {
      if (micGateOpenRef.current) {
        setMicGate(false);
      }
      vadPause();
    }
  }, [status, enabled, setMicGate, vadPause]);

  // Auto-listen mode: restart VAD when idle and gate is open (never during TTS drain).
  useEffect(() => {
    if (!enabled || !AUTO_LISTEN_ENABLED) return;
    if (
      micGateOpen &&
      status === "idle" &&
      !awaitingPlaybackEndRef.current
    ) {
      void vadStart();
    }
  }, [status, enabled, micGateOpen, vadStart]);

  // ---------------- Language change ----------------
  const handleLanguageChange = useCallback(
    (lang: Language) => {
      setLanguage(lang);
      sendJSON({ type: "set_language", language: lang });
      // Stop in-flight playback on language change.
      stopPlayback();
      browserTTS.cancel();
    },
    [browserTTS, sendJSON, setLanguage, stopPlayback],
  );

  const handleVoiceGenderChange = useCallback(
    (g: VoiceGender) => {
      setVoiceGender(g);
      syncVoiceLabel(g);
      sendJSON({ type: "set_voice_gender", voice_gender: g });
      stopPlayback();
      browserTTS.cancel();
    },
    [browserTTS, sendJSON, setVoiceGender, syncVoiceLabel, stopPlayback],
  );

  // Show exact OS voice name when browser TTS fallback is active.
  useEffect(() => {
    if (ttsEngine !== "browser") return;
    const name = browserTTS.activeVoiceName;
    if (!name) return;
    setTtsVoiceInfo({
      label: browserVoiceLabel(name),
      engine: "browser",
    });
  }, [ttsEngine, browserTTS.activeVoiceName, setTtsVoiceInfo]);

  // ---------------- Toggle on/off ----------------
  const handleToggle = useCallback(async () => {
    if (enabled) {
      // Manual mode: first tap after session start opens mic; second tap ends session.
      if (
        !AUTO_LISTEN_ENABLED &&
        !micGateOpenRef.current &&
        status !== "speaking" &&
        status !== "thinking"
      ) {
        openMicForUserTurn();
        return;
      }

      sendJSON({ type: "end_session" });
      setEnabled(false);
      setMicGate(false);
      vad.pause();
      stopCapture();
      stopPlayback();
      browserTTS.cancel();
      if (speechFlushTimerRef.current) {
        clearTimeout(speechFlushTimerRef.current);
        speechFlushTimerRef.current = null;
      }
      if (thinkingWatchdogRef.current) {
        clearTimeout(thinkingWatchdogRef.current);
        thinkingWatchdogRef.current = null;
      }
      awaitingPlaybackEndRef.current = false;
      setStatus("idle");
      return;
    }
    setError(null);
    try {
      await unlockPlayback();
      await startCapture();
      setEnabled(true);
      setStatus("idle");
      if (AUTO_LISTEN_ENABLED) {
        setMicGate(true);
        await vad.start();
      } else {
        setMicGate(false);
      }
    } catch (e) {
      console.error(e);
      const msg = e instanceof Error ? e.message : "Failed to start";
      setError(msg);
      toast.error(msg);
    }
  }, [
    browserTTS,
    enabled,
    openMicForUserTurn,
    setError,
    setMicGate,
    setStatus,
    startCapture,
    status,
    stopCapture,
    stopPlayback,
    unlockPlayback,
    vad,
    sendJSON,
  ]);

  // Prewarm VAD model/worklet right after WS is connected so the first
  // utterance doesn't pay model download/init cost.
  useEffect(() => {
    if (connectionStatus === "connected") {
      void prewarmVAD();
    }
  }, [connectionStatus, prewarmVAD]);


  const handleClearHistory = useCallback(() => {
    sendJSON({ type: "clear_history" });
    clearHistory();
  }, [clearHistory, sendJSON]);

  useEffect(() => {
    if (permissionError) {
      toast.error(`Microphone error: ${permissionError}`);
    }
  }, [permissionError]);

  useEffect(() => {
    return () => {
      if (speechFlushTimerRef.current) {
        clearTimeout(speechFlushTimerRef.current);
      }
      if (thinkingWatchdogRef.current) {
        clearTimeout(thinkingWatchdogRef.current);
      }
      if (playbackEndWatchdogRef.current) {
        clearTimeout(playbackEndWatchdogRef.current);
      }
    };
  }, []);

  const isBotStreaming = status === "thinking" || status === "speaking";

  const connectionLabel = useMemo(() => {
    switch (connection) {
      case "connected":
        return "Connected";
      case "connecting":
        return "Connecting...";
      case "reconnecting":
        return "Reconnecting...";
      case "error":
        return "Connection error";
      default:
        return "Offline";
    }
  }, [connection]);

  const displayTitle = title ?? collegeName;

  return (
    <>
    <div
      className={cn(
        "w-full max-w-5xl overflow-hidden rounded-3xl border bg-zinc-900/50 p-6 shadow-2xl shadow-black/40 backdrop-blur-xl sm:p-8 lg:p-10",
        theme.border,
      )}
    >
      {/* Header */}
      <div className="mb-4 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2 text-zinc-200">
            <Radio className={cn("h-5 w-5 shrink-0", theme.headerIcon)} />
            <h1 className="text-lg font-semibold tracking-tight sm:text-xl">
              {displayTitle}
            </h1>
            <span
              className={cn(
                "text-[10px] uppercase tracking-wider",
                connection === "connected"
                  ? "text-emerald-400"
                  : connection === "error"
                    ? "text-rose-400"
                    : "text-zinc-500",
              )}
            >
              • {connectionLabel}
            </span>
          </div>
          <p className="mt-1 text-xs text-zinc-500">
            {subtitle ?? "Voice AI · LangGraph · Multi-language"}
          </p>
        </div>
        <div className="flex flex-wrap items-center justify-end gap-2 sm:gap-3">
          <VoiceGenderSelector
            value={voiceGender}
            onChange={handleVoiceGenderChange}
            disabled={connection !== "connected"}
            personaNameFemale={personaNameFemale}
            personaNameMale={personaNameMale}
          />
          <LanguageSelector
            value={language}
            onChange={handleLanguageChange}
            disabled={connection !== "connected"}
          />
          <StatusIndicator status={status} latencyMs={latencyMs} />
        </div>
      </div>

      {/* Active TTS voice — exact speaker the user selected / server uses */}
      <div
        className={cn(
          "mb-5 flex flex-col gap-1 rounded-2xl border px-4 py-3 sm:flex-row sm:items-center sm:justify-between",
          theme.border,
          "bg-black/25",
        )}
      >
        <div className="flex min-w-0 items-center gap-3">
          <div
            className={cn(
              "flex h-10 w-10 shrink-0 items-center justify-center rounded-xl",
              status === "speaking"
                ? "bg-amber-500/20 text-amber-300"
                : "bg-white/5 text-zinc-300",
            )}
          >
            <Volume2 className="h-5 w-5" />
          </div>
          <div className="min-w-0">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500">
              {status === "speaking" ? "Speaking with" : "Assistant voice"}
            </p>
            <p
              className="truncate text-sm font-semibold text-zinc-100 sm:text-base sm:whitespace-normal"
              title={ttsVoiceLabel}
            >
              {ttsVoiceLabel}
            </p>
          </div>
        </div>
        {ttsEngine === "sarvam" && ttsSpeaker && (
          <p className="shrink-0 text-[11px] text-zinc-500 sm:text-right">
            Speaker{" "}
            <span className="font-mono text-zinc-300">{ttsSpeaker}</span>
            {ttsModel ? (
              <>
                {" "}
                · Model{" "}
                <span className="font-mono text-zinc-300">{ttsModel}</span>
              </>
            ) : null}
          </p>
        )}
      </div>

      {/* Mic button */}
      <div className="flex flex-col items-center gap-4 overflow-hidden py-6">
        <div className="relative flex h-40 w-40 items-center justify-center overflow-hidden">
          {/* Listening effects: expanding ripples + breathing glow.
              They live OUTSIDE the button so they can overflow it visually. */}
          {enabled && status === "listening" && (
            <>
              {/* Soft breathing glow halo */}
              <span
                aria-hidden
                className={cn(
                  "pointer-events-none absolute inset-0 rounded-full animate-mic-glow",
                  theme.micGlow,
                )}
              />
              <span
                aria-hidden
                className={cn(
                  "pointer-events-none absolute h-28 w-28 rounded-full border-2 animate-mic-ripple",
                  theme.ripple,
                )}
              />
              <span
                aria-hidden
                className={cn(
                  "pointer-events-none absolute h-28 w-28 rounded-full border-2 animate-mic-ripple-delay-1",
                  theme.ripple,
                )}
              />
              <span
                aria-hidden
                className={cn(
                  "pointer-events-none absolute h-28 w-28 rounded-full border-2 animate-mic-ripple-delay-2",
                  theme.ripple,
                )}
              />
            </>
          )}

          <button
            onClick={handleToggle}
            disabled={connection !== "connected" && !enabled}
            className={cn(
              "group relative z-10 flex h-28 w-28 items-center justify-center rounded-full transition-all duration-300",
              "border border-white/10 backdrop-blur",
              enabled
                ? status === "listening"
                  ? theme.micListening
                  : status === "speaking"
                    ? "bg-amber-500/20 shadow-[0_0_50px_rgba(245,158,11,0.35)]"
                    : status === "thinking"
                      ? "bg-purple-500/20 shadow-[0_0_50px_rgba(167,139,250,0.35)]"
                      : theme.micIdle
                : "bg-zinc-800/60 hover:bg-zinc-800",
              "disabled:opacity-50 disabled:cursor-not-allowed",
            )}
            aria-label={enabled ? "Stop" : "Start"}
          >
            {enabled ? (
              <Mic
                className={cn(
                  "h-10 w-10 transition-colors",
                  status === "listening"
                    ? cn(theme.headerIcon, "animate-mic-pulse")
                    : status === "speaking"
                      ? "text-amber-300"
                      : status === "thinking"
                        ? "text-purple-300"
                        : theme.headerIcon,
                )}
              />
            ) : (
              <MicOff className="h-10 w-10 text-zinc-400 group-hover:text-zinc-200" />
            )}
          </button>
        </div>

        <p
          className={cn(
            "text-xs transition-colors duration-300",
            status === "listening" ? theme.subtitle : "text-zinc-500",
          )}
        >
          {!enabled
            ? "Tap the mic to start"
            : !micGateOpen &&
                !AUTO_LISTEN_ENABLED &&
                status !== "speaking" &&
                status !== "thinking"
              ? "Tap mic to speak"
              : status === "listening"
                ? "Listening… speak naturally"
                : status === "thinking"
                  ? "Thinking… mic paused"
                  : status === "speaking"
                    ? "Speaking… mic paused"
                    : AUTO_LISTEN_ENABLED
                      ? "Listening… speak when ready"
                      : "Ready — tap mic to speak"}
        </p>
      </div>

      {/* Visualizer */}
      <div className="mb-4 rounded-xl border border-white/5 bg-black/30 p-3">
        <AudioVisualizer
          analyser={
            status === "speaking" && ttsEngine !== "browser"
              ? playbackAnalyser
              : null
          }
          status={status}
        />
      </div>

      {/* Transcript */}
      <TranscriptPanel
        userTranscript={userTranscript}
        botReply={botReply}
        isBotStreaming={isBotStreaming}
      />

      {/* Footer actions */}
      <div className="mt-4 flex items-center justify-between text-xs">
        <button
          onClick={handleClearHistory}
          className="inline-flex items-center gap-1.5 rounded-md border border-white/10 bg-white/5 px-2.5 py-1.5 text-zinc-300 transition hover:bg-white/10"
        >
          <RotateCcw className="h-3.5 w-3.5" />
          Clear conversation
        </button>

        {errorMessage && (
          <span className="text-rose-400 text-[11px]">{errorMessage}</span>
        )}
      </div>
    </div>
    <SessionReportPanel
      report={sessionReport}
      onClose={() => setSessionReport(null)}
    />
    </>
  );
}
