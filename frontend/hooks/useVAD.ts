"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { MicVAD } from "@ricky0123/vad-web";
import { VAD_REDEMPTION_FRAMES } from "@/lib/voiceConfig";

interface UseVADOptions {
  onSpeechStart?: () => void;
  onSpeechEnd?: () => void;
  onVADMisfire?: () => void;
  startOnLoad?: boolean;
}

interface UseVADReturn {
  isListening: boolean;
  isSpeaking: boolean;
  start: () => Promise<void>;
  prewarm: () => Promise<void>;
  pause: () => void;
  loading: boolean;
  errored: boolean;
}

// All runtime assets are served from /public (copied there by
// `scripts/copy-vad-assets.mjs` which runs before `next dev` / `next build`).
//
// Why local instead of CDN:
//  - onnxruntime-web loads its WASM glue (`ort-wasm-simd-threaded.*.mjs`)
//    via a dynamic `import()`. When bundled by Next.js the URL resolves to
//    `/_next/static/chunks/...` and 404s. Setting `ort.env.wasm.wasmPaths`
//    via the `ortConfig` callback below tells ORT to fetch them from `/`.
//  - The AudioWorklet must be loaded from a same-origin URL on most setups
//    or it fails with a CSP / cross-origin error.
const VAD_WORKLET_URL = "/vad.worklet.bundle.min.js";
const VAD_MODEL_URL = "/silero_vad.onnx";
const ORT_WASM_BASE = "/";

/**
 * Browser-side Silero VAD wrapper around the low-level MicVAD class from
 * `@ricky0123/vad-web`. The MicVAD owns its own MediaStream + audio worklet
 * internally; this is independent of (and runs in parallel with) the
 * AudioWorklet-based capture used to ship audio to the backend.
 *
 * MicVAD is initialised lazily on the first `start()` call so we do not
 * request the microphone before the user has explicitly opted in.
 */
export function useVAD({
  onSpeechStart,
  onSpeechEnd,
  onVADMisfire,
  startOnLoad = false,
}: UseVADOptions = {}): UseVADReturn {
  const vadRef = useRef<MicVAD | null>(null);
  const initPromiseRef = useRef<Promise<MicVAD | null> | null>(null);
  const [loading, setLoading] = useState(false);
  const [errored, setErrored] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isListening, setIsListening] = useState(false);

  const onSpeechStartRef = useRef(onSpeechStart);
  const onSpeechEndRef = useRef(onSpeechEnd);
  const onMisfireRef = useRef(onVADMisfire);
  useEffect(() => {
    onSpeechStartRef.current = onSpeechStart;
  }, [onSpeechStart]);
  useEffect(() => {
    onSpeechEndRef.current = onSpeechEnd;
  }, [onSpeechEnd]);
  useEffect(() => {
    onMisfireRef.current = onVADMisfire;
  }, [onVADMisfire]);

  const ensureVAD = useCallback(async (): Promise<MicVAD | null> => {
    if (vadRef.current) return vadRef.current;
    if (initPromiseRef.current) return initPromiseRef.current;

    setLoading(true);
    const promise = (async () => {
      try {
        const vadOpts = {
          // Wait longer in silence before auto stop (see VAD_REDEMPTION_FRAMES).
          positiveSpeechThreshold: 0.5,
          negativeSpeechThreshold: 0.35,
          minSpeechFrames: 3,
          redemptionFrames: VAD_REDEMPTION_FRAMES,
          preSpeechPadFrames: 6,
          onSpeechStart: () => {
            setIsSpeaking(true);
            onSpeechStartRef.current?.();
          },
          onSpeechEnd: () => {
            setIsSpeaking(false);
            onSpeechEndRef.current?.();
          },
          onVADMisfire: () => {
            setIsSpeaking(false);
            onMisfireRef.current?.();
          },
          // Explicit URLs so Next.js doesn't try to resolve these as chunks.
          workletURL: VAD_WORKLET_URL,
          modelURL: VAD_MODEL_URL,
          // The real hook for telling onnxruntime-web where to fetch its
          // WASM-loader `.mjs` and `.wasm` files. Maps to ort.env.wasm.
          ortConfig: (ort: {
            env: { wasm: { wasmPaths: string; numThreads?: number } };
          }) => {
            ort.env.wasm.wasmPaths = ORT_WASM_BASE;
            // Threading via SharedArrayBuffer isn't available without
            // COOP/COEP headers; force single-threaded to avoid a warning.
            ort.env.wasm.numThreads = 1;
          },
        };
        const vad = await MicVAD.new(
          vadOpts as unknown as Parameters<typeof MicVAD.new>[0],
        );
        vadRef.current = vad;
        return vad;
      } catch (e) {
        console.error("[vad] init failed", e);
        setErrored(true);
        return null;
      } finally {
        setLoading(false);
      }
    })();

    initPromiseRef.current = promise;
    return promise;
  }, []);

  const start = useCallback(async () => {
    try {
      const vad = await ensureVAD();
      if (!vad) return;
      vad.start();
      setIsListening(true);
      setErrored(false);
    } catch (e) {
      console.error("[vad] start failed", e);
      setErrored(true);
    }
  }, [ensureVAD]);

  const prewarm = useCallback(async () => {
    await ensureVAD();
  }, [ensureVAD]);

  const pause = useCallback(() => {
    try {
      vadRef.current?.pause();
    } catch {
      // ignore
    }
    setIsListening(false);
    setIsSpeaking(false);
  }, []);

  useEffect(() => {
    if (startOnLoad) {
      void start();
    }
    return () => {
      try {
        vadRef.current?.destroy();
      } catch {
        // ignore
      }
      vadRef.current = null;
      initPromiseRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return {
    isListening,
    isSpeaking,
    start,
    prewarm,
    pause,
    loading,
    errored,
  };
}
