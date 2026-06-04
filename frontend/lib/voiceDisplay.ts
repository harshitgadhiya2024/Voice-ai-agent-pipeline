import type { VoiceGender } from "@/types";

/** Sarvam Bulbul v3 — must match backend/config.py SARVAM_VOICES + sarvam_model. */
export const SARVAM_TTS_MODEL = "bulbul:v3";

export const SARVAM_SPEAKER_BY_GENDER: Record<VoiceGender, string> = {
  female: "priya",
  male: "rahul",
};

export function sarvamSpeakerId(gender: VoiceGender): string {
  return SARVAM_SPEAKER_BY_GENDER[gender] ?? "priya";
}

/** Sarvam speaker display name only. */
export function sarvamSpeakerLabel(gender: VoiceGender): string {
  const speaker = sarvamSpeakerId(gender);
  return speaker.charAt(0).toUpperCase() + speaker.slice(1);
}

/** Human-readable TTS line (Sarvam engine). */
export function sarvamVoiceLabel(gender: VoiceGender): string {
  return `Sarvam · ${sarvamSpeakerLabel(gender)} · ${SARVAM_TTS_MODEL}`;
}

/** Persona + Sarvam — what each demo shows in the voice bar. */
export function assistantVoiceLabel(
  gender: VoiceGender,
  personaFemale: string,
  personaMale: string,
): string {
  const persona = gender === "male" ? personaMale : personaFemale;
  return `${persona} · Sarvam ${sarvamSpeakerLabel(gender)} · ${SARVAM_TTS_MODEL}`;
}

export function personaForGender(
  gender: VoiceGender,
  personaFemale: string,
  personaMale: string,
): string {
  return gender === "male" ? personaMale : personaFemale;
}

export function browserVoiceLabel(osVoiceName: string | null): string {
  if (!osVoiceName?.trim()) return "Browser speech (OS voice)";
  return `Browser · ${osVoiceName.trim()}`;
}
