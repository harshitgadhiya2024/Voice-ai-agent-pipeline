/**
 * When true: VAD runs continuously whenever the bot is idle (auto-detect speech).
 * When false (default): mic opens only after TTS playback finishes, or when the
 * user taps the mic button to speak.
 *
 * Set in frontend/.env.local:
 *   NEXT_PUBLIC_AUTO_LISTEN=true
 */
export const AUTO_LISTEN_ENABLED =
  process.env.NEXT_PUBLIC_AUTO_LISTEN === "true";

/** Silero VAD frames (~96ms each at 16kHz) to wait after speech drops before end-of-utterance. */
function parseVadFrames(
  raw: string | undefined,
  fallback: number,
): number {
  const n = parseInt(raw ?? "", 10);
  if (Number.isFinite(n) && n >= 2 && n <= 40) return n;
  return fallback;
}

/**
 * How long silence must last before auto stop (approx).
 * redemptionFrames × ~96ms — default 14 ≈ 1.3s.
 *
 *   NEXT_PUBLIC_VAD_REDEMPTION_FRAMES=18
 */
export const VAD_REDEMPTION_FRAMES = parseVadFrames(
  process.env.NEXT_PUBLIC_VAD_REDEMPTION_FRAMES,
  14,
);

/** Extra ms after VAD end before flipping UI to "thinking" (mic flush to server). */
export const SPEECH_END_FLUSH_MS = (() => {
  const n = parseInt(process.env.NEXT_PUBLIC_SPEECH_END_FLUSH_MS ?? "", 10);
  return Number.isFinite(n) && n >= 0 && n <= 2000 ? n : 450;
})();

/** Playback debounce between TTS WebSocket chunks (ms). */
export const TTS_PLAYBACK_GAP_MS = (() => {
  const n = parseInt(process.env.NEXT_PUBLIC_TTS_PLAYBACK_GAP_MS ?? "", 10);
  return Number.isFinite(n) && n >= 100 && n <= 1200 ? n : 500;
})();
