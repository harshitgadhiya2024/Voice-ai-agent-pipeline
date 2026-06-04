"use client";

import Link from "next/link";
import { ArrowRight, Database, Mic } from "lucide-react";

import { UseCaseIcon } from "@/components/UseCaseIcon";
import { personaForGender, sarvamSpeakerLabel } from "@/lib/voiceDisplay";
import { accentStyles } from "@/lib/useCases";
import { cn } from "@/lib/utils";
import type { UseCaseMetadata } from "@/types/useCase";

interface UseCaseGalleryProps {
  useCases: UseCaseMetadata[];
}

export function UseCaseGallery({ useCases }: UseCaseGalleryProps) {
  return (
    <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-3">
      {useCases.map((uc) => (
        <UseCaseCard key={uc.id} useCase={uc} />
      ))}
    </div>
  );
}

function UseCaseCard({ useCase }: { useCase: UseCaseMetadata }) {
  const styles = accentStyles(useCase.accent);
  const records = useCase.knowledge_records ?? 0;
  const persona = personaForGender(
    useCase.default_voice_gender,
    useCase.persona_name_female,
    useCase.persona_name_male,
  );
  const speaker = sarvamSpeakerLabel(useCase.default_voice_gender);

  return (
    <Link
      href={`/demo/${useCase.id}`}
      className={cn(
        "group relative flex flex-col overflow-hidden rounded-3xl border border-white/10 bg-zinc-900/60 p-6 shadow-xl shadow-black/40 backdrop-blur-xl transition-transform duration-300 hover:-translate-y-1 hover:border-white/20",
        "ring-0 hover:ring-2",
        styles.ring,
      )}
    >
      <div
        className={cn(
          "pointer-events-none absolute inset-0 -z-10 bg-gradient-to-br opacity-80",
          styles.cardGlow,
        )}
      />

      <div className="flex items-start justify-between gap-3">
        <div
          className={cn(
            "flex h-12 w-12 items-center justify-center rounded-xl",
            styles.icon,
          )}
        >
          <UseCaseIcon name={useCase.icon} className="h-6 w-6" />
        </div>
        <span
          className={cn(
            "rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.18em]",
            styles.badge,
          )}
        >
          {useCase.company}
        </span>
      </div>

      <h3 className="mt-5 text-lg font-semibold tracking-tight text-white">
        {useCase.name}
      </h3>
      <p className="mt-1 text-sm text-zinc-400">{useCase.tagline}</p>
      <p className="mt-3 line-clamp-3 text-[13px] leading-relaxed text-zinc-400">
        {useCase.description}
      </p>

      <div className="mt-5 flex flex-wrap gap-1.5">
        {useCase.intents.slice(0, 4).map((i) => (
          <span
            key={i.id}
            className="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] text-zinc-400"
          >
            {i.label}
          </span>
        ))}
      </div>

      <div className="mt-6 flex items-center justify-between">
        <div className="flex flex-wrap items-center gap-3 text-[11px] text-zinc-500">
          <span className="inline-flex items-center gap-1" title={`${persona} · Sarvam ${speaker}`}>
            <Mic className="h-3 w-3" />
            {persona} · {speaker}
          </span>
          {records > 0 && (
            <span className="inline-flex items-center gap-1">
              <Database className="h-3 w-3" />
              {records.toLocaleString()}+ facts
            </span>
          )}
        </div>
        <span className="inline-flex items-center gap-1.5 text-xs font-medium text-zinc-200 transition-colors group-hover:text-white">
          Try demo <ArrowRight className="h-3.5 w-3.5" />
        </span>
      </div>
    </Link>
  );
}
