"use client";

import dynamic from "next/dynamic";
import { Database, MapPin } from "lucide-react";

import { UseCaseIcon } from "@/components/UseCaseIcon";
import { accentStyles } from "@/lib/useCases";
import { cn } from "@/lib/utils";
import type { UseCaseMetadata } from "@/types/useCase";

const VoiceBot = dynamic(
  () => import("@/components/VoiceBot").then((m) => m.VoiceBot),
  { ssr: false },
);

interface DemoWorkspaceProps {
  useCase: UseCaseMetadata;
}

export function DemoWorkspace({ useCase }: DemoWorkspaceProps) {
  const styles = accentStyles(useCase.accent);
  const records = useCase.knowledge_records ?? 0;

  return (
    <div className="flex flex-col gap-8">
      <header
        className={cn(
          "relative overflow-hidden rounded-3xl border border-white/10 bg-zinc-900/60 p-6 backdrop-blur-xl sm:p-8",
        )}
      >
        <div
          className={cn(
            "pointer-events-none absolute inset-0 -z-10 bg-gradient-to-br opacity-70",
            styles.cardGlow,
          )}
        />
        <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
          <div className="flex items-start gap-4">
            <div
              className={cn(
                "flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl",
                styles.icon,
              )}
            >
              <UseCaseIcon name={useCase.icon} className="h-7 w-7" />
            </div>
            <div>
              <span
                className={cn(
                  "rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.18em]",
                  styles.badge,
                )}
              >
                {useCase.company}
              </span>
              <h1 className="mt-2 text-2xl font-semibold tracking-tight text-white sm:text-3xl">
                {useCase.name}
              </h1>
              <p className="mt-1 text-sm text-zinc-400">{useCase.tagline}</p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2 lg:flex-col lg:items-end">
            {records > 0 && (
              <span
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs",
                  styles.badge,
                )}
              >
                <Database className="h-3.5 w-3.5" />
                {records >= 1000
                  ? `${records.toLocaleString()}+ knowledge records`
                  : `${records.toLocaleString()} knowledge records`}
              </span>
            )}
            <span className="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-zinc-400">
              <MapPin className="h-3.5 w-3.5" />
              15+ cities · multi-scenario
            </span>
          </div>
        </div>

        <p className="mt-5 max-w-3xl text-sm leading-relaxed text-zinc-400">
          {useCase.description}
        </p>

        <div className="mt-5 flex flex-wrap gap-2">
          {useCase.intents.map((i) => (
            <span
              key={i.id}
              className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] text-zinc-300"
              title={i.description}
            >
              {i.label}
            </span>
          ))}
        </div>

        <div className="mt-6">
          <p className="mb-2 text-[10px] uppercase tracking-wider text-zinc-500">
            Try saying
          </p>
          <div className="flex flex-wrap gap-2">
            {useCase.sample_questions.slice(0, 5).map((q) => (
              <span
                key={q}
                className="max-w-full rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-[12px] leading-snug text-zinc-300"
              >
                {q}
              </span>
            ))}
          </div>
        </div>
      </header>

      <div className="mx-auto w-full max-w-5xl">
        <VoiceBot
          useCaseId={useCase.id}
          accent={useCase.accent}
          title={`${useCase.name} — ${useCase.company}`}
          subtitle={`Agentic voice · ${useCase.intents.length} specialists · EN / HI / GU`}
          defaultVoiceGender={useCase.default_voice_gender}
          personaNameFemale={useCase.persona_name_female}
          personaNameMale={useCase.persona_name_male}
        />
      </div>
    </div>
  );
}
