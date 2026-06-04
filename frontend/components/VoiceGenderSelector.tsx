"use client";

import { useEffect, useRef, useState } from "react";
import { ChevronDown, Volume2 } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  assistantVoiceLabel,
  personaForGender,
  sarvamSpeakerLabel,
} from "@/lib/voiceDisplay";
import type { VoiceGender } from "@/types";

interface VoiceGenderSelectorProps {
  value: VoiceGender;
  onChange: (g: VoiceGender) => void;
  disabled?: boolean;
  personaNameFemale?: string;
  personaNameMale?: string;
}

/** Select Sarvam TTS voice (Priya / Rahul) with per-demo persona names. */
export function VoiceGenderSelector({
  value,
  onChange,
  disabled,
  personaNameFemale = "Priya",
  personaNameMale = "Rahul",
}: VoiceGenderSelectorProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (!ref.current) return;
      if (!ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  const currentPersona = personaForGender(
    value,
    personaNameFemale,
    personaNameMale,
  );
  const fullLabel = assistantVoiceLabel(
    value,
    personaNameFemale,
    personaNameMale,
  );
  const accent = value === "female" ? "text-pink-300" : "text-sky-300";

  return (
    <div ref={ref} className="relative min-w-0">
      <button
        type="button"
        disabled={disabled}
        onClick={() => setOpen((v) => !v)}
        className={cn(
          "inline-flex max-w-full items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-2 text-left text-xs font-medium text-zinc-200 transition hover:bg-white/10 backdrop-blur",
          disabled && "opacity-50 cursor-not-allowed",
        )}
        title={fullLabel}
        aria-label={`Voice: ${fullLabel}`}
      >
        <Volume2 className={cn("h-4 w-4 shrink-0", accent)} />
        <span className="min-w-0 truncate sm:max-w-[200px]">
          {currentPersona} · {sarvamSpeakerLabel(value)}
        </span>
        <ChevronDown
          className={cn(
            "h-3.5 w-3.5 shrink-0 text-zinc-400 transition",
            open && "rotate-180",
          )}
        />
      </button>

      {open && (
        <div className="absolute right-0 z-30 mt-2 w-72 overflow-hidden rounded-xl border border-white/10 bg-zinc-900/95 shadow-xl shadow-black/40 backdrop-blur-xl">
          <div className="border-b border-white/5 px-3 py-2">
            <p className="text-[10px] uppercase tracking-wider text-zinc-500">
              TTS voice (Sarvam bulbul:v3)
            </p>
            <p className="mt-0.5 text-[11px] text-zinc-400">{fullLabel}</p>
          </div>
          {(["female", "male"] as const).map((code) => {
            const active = code === value;
            const optAccent =
              code === "female" ? "text-pink-300" : "text-sky-300";
            const persona = personaForGender(
              code,
              personaNameFemale,
              personaNameMale,
            );
            const optFull = assistantVoiceLabel(
              code,
              personaNameFemale,
              personaNameMale,
            );
            return (
              <button
                key={code}
                type="button"
                onClick={() => {
                  onChange(code);
                  setOpen(false);
                }}
                className={cn(
                  "flex w-full flex-col items-start gap-0.5 px-3 py-2.5 text-left text-xs transition",
                  active
                    ? "bg-teal-500/15 text-teal-100"
                    : "text-zinc-200 hover:bg-white/5",
                )}
              >
                <span className="flex w-full items-center justify-between font-semibold">
                  {persona} · {sarvamSpeakerLabel(code)}
                  <Volume2 className={cn("h-3.5 w-3.5", optAccent)} />
                </span>
                <span className="text-[10px] text-zinc-500">{optFull}</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
