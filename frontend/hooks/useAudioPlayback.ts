"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { pcm16BufferToFloat32 } from "@/lib/audioUtils";
import { TTS_PLAYBACK_GAP_MS } from "@/lib/voiceConfig";

interface UseAudioPlaybackOptions {
  /** Initial / default sample rate. Real rate is taken from `tts_start` messages. */
  sampleRate?: number;
  onPlaybackStart?: () => void;
  onPlaybackEnd?: () => void;
}

interface UseAudioPlaybackReturn {
  enqueueAudio: (data: ArrayBuffer) => void;
  stopPlayback: () => void;
  isPlaying: boolean;
  audioContext: AudioContext | null;
  analyser: AnalyserNode | null;
  unlock: () => Promise<void>;
  /** Set the sample rate for incoming chunks (matches the engine's output). */
  setSampleRate: (rate: number) => void;
  /** Call when a new TTS utterance begins (tts_start). */
  resetStream: () => void;
  /** Call when the server finished sending audio (tts_end). */
  markStreamComplete: () => void;
}

/** Grace period after the last buffer ends — absorbs gaps between WS chunks. */
const INTER_CHUNK_GAP_MS = TTS_PLAYBACK_GAP_MS;

/**
 * Gapless streaming PCM playback using scheduled AudioBufferSourceNodes.
 *
 * `onPlaybackEnd` fires only after `markStreamComplete()` AND all scheduled
 * buffers have finished, plus a short debounce so inter-chunk network gaps
 * do not reopen the mic mid-sentence.
 */
export function useAudioPlayback({
  sampleRate: defaultSampleRate = 24000,
  onPlaybackStart,
  onPlaybackEnd,
}: UseAudioPlaybackOptions = {}): UseAudioPlaybackReturn {
  const ctxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const gainRef = useRef<GainNode | null>(null);
  const nextStartRef = useRef<number>(0);
  const activeSourcesRef = useRef<Set<AudioBufferSourceNode>>(new Set());
  const endDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const currentRateRef = useRef<number>(defaultSampleRate);
  const streamCompleteRef = useRef(false);
  const utteranceActiveRef = useRef(false);
  const playbackEndedRef = useRef(false);
  const onPlaybackEndRef = useRef(onPlaybackEnd);
  const onPlaybackStartRef = useRef(onPlaybackStart);
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    onPlaybackEndRef.current = onPlaybackEnd;
  }, [onPlaybackEnd]);
  useEffect(() => {
    onPlaybackStartRef.current = onPlaybackStart;
  }, [onPlaybackStart]);

  const ensureContext = useCallback((): AudioContext => {
    if (ctxRef.current) return ctxRef.current;
    const AudioCtxCtor =
      (window as unknown as { webkitAudioContext?: typeof AudioContext })
        .webkitAudioContext || window.AudioContext;
    const ctx = new AudioCtxCtor();
    const gain = ctx.createGain();
    gain.gain.value = 1.0;
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 256;
    gain.connect(analyser);
    analyser.connect(ctx.destination);
    ctxRef.current = ctx;
    gainRef.current = gain;
    analyserRef.current = analyser;
    nextStartRef.current = ctx.currentTime;
    return ctx;
  }, []);

  const unlock = useCallback(async () => {
    const ctx = ensureContext();
    if (ctx.state === "suspended") {
      try {
        await ctx.resume();
      } catch (e) {
        console.warn("[playback] resume failed", e);
      }
    }
  }, [ensureContext]);

  const clearEndDebounce = useCallback(() => {
    if (endDebounceRef.current) {
      clearTimeout(endDebounceRef.current);
      endDebounceRef.current = null;
    }
  }, []);

  const firePlaybackEnd = useCallback(() => {
    if (playbackEndedRef.current) return;
    playbackEndedRef.current = true;
    utteranceActiveRef.current = false;
    setIsPlaying(false);
    onPlaybackEndRef.current?.();
  }, []);

  const schedulePlaybackEndCheck = useCallback(() => {
    clearEndDebounce();

    // Never signal end until the server sent tts_end.
    if (!streamCompleteRef.current) return;
    if (playbackEndedRef.current) return;

    const ctx = ctxRef.current;
    if (!ctx) {
      endDebounceRef.current = setTimeout(() => {
        schedulePlaybackEndCheck();
      }, INTER_CHUNK_GAP_MS);
      return;
    }

    // Buffers still scheduled in the audio context — wait until they finish.
    if (activeSourcesRef.current.size > 0) {
      const msUntilScheduledEnd = Math.max(
        0,
        (nextStartRef.current - ctx.currentTime) * 1000,
      );
      endDebounceRef.current = setTimeout(() => {
        schedulePlaybackEndCheck();
      }, msUntilScheduledEnd + 40);
      return;
    }

    // Queue drained and stream complete — debounce in case another chunk arrives.
    endDebounceRef.current = setTimeout(() => {
      endDebounceRef.current = null;
      if (!streamCompleteRef.current || playbackEndedRef.current) return;
      if (activeSourcesRef.current.size > 0) {
        schedulePlaybackEndCheck();
        return;
      }
      firePlaybackEnd();
    }, INTER_CHUNK_GAP_MS);
  }, [clearEndDebounce, firePlaybackEnd]);

  const resetStream = useCallback(() => {
    streamCompleteRef.current = false;
    utteranceActiveRef.current = false;
    playbackEndedRef.current = false;
    clearEndDebounce();
  }, [clearEndDebounce]);

  const markStreamComplete = useCallback(() => {
    streamCompleteRef.current = true;
    schedulePlaybackEndCheck();
  }, [schedulePlaybackEndCheck]);

  const setSampleRate = useCallback((rate: number) => {
    if (rate > 0 && rate !== currentRateRef.current) {
      currentRateRef.current = rate;
    }
  }, []);

  const enqueueAudio = useCallback(
    (data: ArrayBuffer) => {
      if (!data || data.byteLength === 0) return;

      // New chunk arrived — cancel any pending "playback ended" debounce.
      clearEndDebounce();
      playbackEndedRef.current = false;

      const ctx = ensureContext();
      const sampleRate = currentRateRef.current || defaultSampleRate;

      const samples = pcm16BufferToFloat32(data);
      if (samples.length === 0) return;

      let buffer: AudioBuffer;
      try {
        buffer = ctx.createBuffer(1, samples.length, sampleRate);
      } catch (e) {
        console.warn(
          "[playback] createBuffer failed at",
          sampleRate,
          "falling back",
          e,
        );
        buffer = ctx.createBuffer(1, samples.length, 24000);
      }
      buffer.copyToChannel(samples, 0, 0);

      const source = ctx.createBufferSource();
      source.buffer = buffer;
      source.connect(gainRef.current!);

      const now = ctx.currentTime;
      const startAt = Math.max(nextStartRef.current, now);
      source.start(startAt);
      nextStartRef.current = startAt + buffer.duration;

      activeSourcesRef.current.add(source);
      source.onended = () => {
        activeSourcesRef.current.delete(source);
        schedulePlaybackEndCheck();
      };

      if (!utteranceActiveRef.current) {
        utteranceActiveRef.current = true;
        setIsPlaying(true);
        onPlaybackStartRef.current?.();
      }
    },
    [
      clearEndDebounce,
      defaultSampleRate,
      ensureContext,
      schedulePlaybackEndCheck,
    ],
  );

  const stopPlayback = useCallback(() => {
    clearEndDebounce();
    const sources = Array.from(activeSourcesRef.current);
    activeSourcesRef.current.clear();
    for (const s of sources) {
      try {
        s.onended = null;
        s.stop();
      } catch {
        // ignore
      }
      try {
        s.disconnect();
      } catch {
        // ignore
      }
    }
    if (ctxRef.current) {
      nextStartRef.current = ctxRef.current.currentTime;
    }
    utteranceActiveRef.current = false;
    setIsPlaying(false);
  }, [clearEndDebounce]);

  useEffect(() => {
    return () => {
      stopPlayback();
      if (ctxRef.current) {
        try {
          void ctxRef.current.close();
        } catch {
          // ignore
        }
        ctxRef.current = null;
      }
    };
  }, [stopPlayback]);

  return {
    enqueueAudio,
    stopPlayback,
    isPlaying,
    audioContext: ctxRef.current,
    analyser: analyserRef.current,
    unlock,
    setSampleRate,
    resetStream,
    markStreamComplete,
  };
};
