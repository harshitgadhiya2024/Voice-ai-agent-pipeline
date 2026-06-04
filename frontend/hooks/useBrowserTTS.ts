"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { Language } from "@/types";
import { SPEECH_LOCALE } from "@/types";

interface UseBrowserTTSOptions {
  onStart?: () => void;
  onEnd?: () => void;
  /** Prefer OS voices that match this gender when falling back to browser TTS. */
  voiceGender?: "female" | "male";
}

interface UseBrowserTTSReturn {
  /** OS voice name used for the last / current utterance. */
  activeVoiceName: string | null;
  /** Queue a sentence to be spoken in the given language. */
  speak: (text: string, language: Language) => void;
  /** Stop everything in the queue immediately. */
  cancel: () => void;
  /** Mark the current speech queue as complete; fires onEnd when drained. */
  flush: () => void;
  isSpeaking: boolean;
  isSupported: boolean;
  availableLanguages: Set<string>;
}

/**
 * Streaming-friendly wrapper around `window.speechSynthesis`. Used for Hindi,
 * Browser fallback if backend TTS fails or returns no audio.
 *
 * Behaviour:
 * - Each call to `speak()` enqueues an utterance.
 * - We pick the best voice for the requested language from the OS list.
 * - `flush()` indicates "no more sentences coming"; the hook fires `onEnd`
 *   after the last queued utterance finishes.
 * - `cancel()` halts everything (used for barge-in).
 */
export function useBrowserTTS({
  onStart,
  onEnd,
  voiceGender = "female",
}: UseBrowserTTSOptions = {}): UseBrowserTTSReturn {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [activeVoiceName, setActiveVoiceName] = useState<string | null>(null);
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [isSupported, setIsSupported] = useState(false);

  const queueLengthRef = useRef(0);
  const flushedRef = useRef(false);
  const onStartRef = useRef(onStart);
  const onEndRef = useRef(onEnd);
  useEffect(() => {
    onStartRef.current = onStart;
  }, [onStart]);
  useEffect(() => {
    onEndRef.current = onEnd;
  }, [onEnd]);

  // Load voices (some browsers populate them asynchronously).
  useEffect(() => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      setIsSupported(false);
      return;
    }
    setIsSupported(true);
    const load = () => setVoices(window.speechSynthesis.getVoices());
    load();
    window.speechSynthesis.addEventListener("voiceschanged", load);
    return () => {
      window.speechSynthesis.removeEventListener("voiceschanged", load);
    };
  }, []);

  const availableLanguages = (() => {
    const s = new Set<string>();
    for (const v of voices) s.add(v.lang.toLowerCase());
    return s;
  })();

  const pickVoice = useCallback(
    (language: Language): SpeechSynthesisVoice | null => {
      const targetLocale = SPEECH_LOCALE[language] || "en-US";
      const targetPrefix = targetLocale.toLowerCase().slice(0, 2);
      const wantFemale = voiceGender === "female";

      const score = (v: SpeechSynthesisVoice): number => {
        let s = 0;
        const name = v.name.toLowerCase();
        const lang = v.lang.toLowerCase();
        if (lang === targetLocale.toLowerCase()) s += 4;
        else if (lang.startsWith(targetPrefix)) s += 2;
        if (wantFemale) {
          if (/female|woman|priya|veena|lekha|kavya|samantha|zira|sangeeta/.test(name)) {
            s += 3;
          }
          if (/male|man|david|mark|ravi|rahul|alex/.test(name)) s -= 2;
        } else {
          if (/male|man|david|mark|ravi|rahul|alex/.test(name)) s += 3;
          if (/female|woman|priya|veena|zira/.test(name)) s -= 2;
        }
        if (v.default) s += 1;
        return s;
      };

      if (voices.length === 0) return null;
      return [...voices].sort((a, b) => score(b) - score(a))[0] ?? null;
    },
    [voices, voiceGender],
  );

  const speak = useCallback(
    (text: string, language: Language) => {
      const clean = text.trim();
      if (!clean) return;
      if (typeof window === "undefined" || !window.speechSynthesis) return;

      const utter = new SpeechSynthesisUtterance(clean);
      utter.lang = SPEECH_LOCALE[language] || "en-US";
      const voice = pickVoice(language);
      if (voice) {
        utter.voice = voice;
        setActiveVoiceName(voice.name);
      }
      utter.rate = 1.0;
      utter.pitch = 1.0;
      utter.volume = 1.0;

      const wasIdle = queueLengthRef.current === 0;
      queueLengthRef.current += 1;
      flushedRef.current = false;

      utter.onstart = () => {
        if (wasIdle) {
          setIsSpeaking(true);
          onStartRef.current?.();
        }
      };
      const finish = () => {
        queueLengthRef.current = Math.max(0, queueLengthRef.current - 1);
        if (queueLengthRef.current === 0 && flushedRef.current) {
          setIsSpeaking(false);
          onEndRef.current?.();
        }
      };
      utter.onend = finish;
      utter.onerror = finish;

      try {
        window.speechSynthesis.speak(utter);
      } catch (e) {
        console.warn("[browser-tts] speak failed", e);
        finish();
      }
    },
    [pickVoice],
  );

  const cancel = useCallback(() => {
    if (typeof window === "undefined" || !window.speechSynthesis) return;
    try {
      window.speechSynthesis.cancel();
    } catch {
      // ignore
    }
    queueLengthRef.current = 0;
    flushedRef.current = false;
    setIsSpeaking(false);
    setActiveVoiceName(null);
  }, []);

  const flush = useCallback(() => {
    flushedRef.current = true;
    // If nothing was ever queued, fire onEnd immediately so callers get
    // their idle signal.
    if (queueLengthRef.current === 0) {
      if (isSpeaking) setIsSpeaking(false);
      onEndRef.current?.();
    }
  }, [isSpeaking]);

  // Tidy up on unmount.
  useEffect(() => {
    return () => {
      if (typeof window !== "undefined" && window.speechSynthesis) {
        try {
          window.speechSynthesis.cancel();
        } catch {
          // ignore
        }
      }
    };
  }, []);

  return {
    activeVoiceName,
    speak,
    cancel,
    flush,
    isSpeaking,
    isSupported,
    availableLanguages,
  };
}
