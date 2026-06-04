"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  float32ToPCM16Buffer,
  resampleFloat32,
} from "@/lib/audioUtils";

const PCM_WORKLET_CODE = `
class PCMProcessor extends AudioWorkletProcessor {
  process(inputs) {
    const input = inputs[0];
    if (input && input[0]) {
      // Clone because the underlying buffer is reused.
      const channel = input[0];
      const copy = new Float32Array(channel.length);
      copy.set(channel);
      this.port.postMessage(copy, [copy.buffer]);
    }
    return true;
  }
}
registerProcessor('pcm-processor', PCMProcessor);
`;

interface UseAudioCaptureOptions {
  /** Target sample rate to send to backend. */
  targetSampleRate?: number;
  /** Called with 16-bit PCM little-endian ArrayBuffer chunks. */
  onPcmChunk?: (pcm: ArrayBuffer) => void;
  /** Called with the raw MediaStream once granted (for visualizers etc.). */
  onStream?: (stream: MediaStream) => void;
  /** When false the worklet still runs but onPcmChunk is suppressed. */
  enabled?: boolean;
}

interface UseAudioCaptureReturn {
  start: () => Promise<void>;
  stop: () => void;
  isCapturing: boolean;
  permissionError: string | null;
  mediaStream: MediaStream | null;
  audioContext: AudioContext | null;
  sourceNode: MediaStreamAudioSourceNode | null;
}

/**
 * Capture mic audio via AudioWorklet, resample to `targetSampleRate`, and
 * deliver 16-bit PCM little-endian ArrayBuffer chunks.
 */
export function useAudioCapture({
  targetSampleRate = 16000,
  onPcmChunk,
  onStream,
  enabled = true,
}: UseAudioCaptureOptions = {}): UseAudioCaptureReturn {
  const audioCtxRef = useRef<AudioContext | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const workletRef = useRef<AudioWorkletNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const enabledRef = useRef(enabled);
  const onChunkRef = useRef(onPcmChunk);
  const onStreamRef = useRef(onStream);

  const [isCapturing, setIsCapturing] = useState(false);
  const [permissionError, setPermissionError] = useState<string | null>(null);

  useEffect(() => {
    enabledRef.current = enabled;
    // Hard-mute capture tracks while bot thinks/speaks (half-duplex).
    if (streamRef.current) {
      for (const track of streamRef.current.getAudioTracks()) {
        track.enabled = enabled;
      }
    }
  }, [enabled]);
  useEffect(() => {
    onChunkRef.current = onPcmChunk;
  }, [onPcmChunk]);
  useEffect(() => {
    onStreamRef.current = onStream;
  }, [onStream]);

  const start = useCallback(async () => {
    if (audioCtxRef.current) return;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
        video: false,
      });
      streamRef.current = stream;
      onStreamRef.current?.(stream);

      const AudioCtxCtor =
        (window as unknown as { webkitAudioContext?: typeof AudioContext })
          .webkitAudioContext || window.AudioContext;
      // Note: not all browsers honor `sampleRate` in AudioContext constructor;
      // we resample manually below.
      const audioCtx = new AudioCtxCtor();
      audioCtxRef.current = audioCtx;

      const blob = new Blob([PCM_WORKLET_CODE], {
        type: "application/javascript",
      });
      const workletUrl = URL.createObjectURL(blob);
      await audioCtx.audioWorklet.addModule(workletUrl);
      URL.revokeObjectURL(workletUrl);

      const source = audioCtx.createMediaStreamSource(stream);
      sourceRef.current = source;

      const node = new AudioWorkletNode(audioCtx, "pcm-processor");
      workletRef.current = node;

      const inputRate = audioCtx.sampleRate;
      node.port.onmessage = (ev: MessageEvent<Float32Array>) => {
        if (!enabledRef.current) return;
        const chunk = ev.data;
        const resampled =
          inputRate === targetSampleRate
            ? chunk
            : resampleFloat32(chunk, inputRate, targetSampleRate);
        const pcm = float32ToPCM16Buffer(resampled);
        onChunkRef.current?.(pcm);
      };

      source.connect(node);
      // Connect worklet to destination through a muted gain to keep it alive
      // without producing any audible output.
      const silentGain = audioCtx.createGain();
      silentGain.gain.value = 0;
      node.connect(silentGain).connect(audioCtx.destination);

      setIsCapturing(true);
      setPermissionError(null);
    } catch (e) {
      console.error("[capture] failed", e);
      const msg =
        e instanceof Error ? e.message : "Failed to access microphone";
      setPermissionError(msg);
      setIsCapturing(false);
    }
  }, [targetSampleRate]);

  const stop = useCallback(() => {
    try {
      workletRef.current?.disconnect();
    } catch {
      // ignore
    }
    workletRef.current = null;
    try {
      sourceRef.current?.disconnect();
    } catch {
      // ignore
    }
    sourceRef.current = null;
    if (streamRef.current) {
      for (const track of streamRef.current.getTracks()) {
        try {
          track.stop();
        } catch {
          // ignore
        }
      }
      streamRef.current = null;
    }
    if (audioCtxRef.current) {
      try {
        void audioCtxRef.current.close();
      } catch {
        // ignore
      }
      audioCtxRef.current = null;
    }
    setIsCapturing(false);
  }, []);

  useEffect(() => {
    return () => stop();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return {
    start,
    stop,
    isCapturing,
    permissionError,
    mediaStream: streamRef.current,
    audioContext: audioCtxRef.current,
    sourceNode: sourceRef.current,
  };
}
