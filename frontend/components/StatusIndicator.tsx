"use client";

import { cn } from "@/lib/utils";
import type { VoiceStatus } from "@/types";

interface StatusIndicatorProps {
  status: VoiceStatus;
  latencyMs?: number | null;
}

const STATUS_CONFIG: Record<
  VoiceStatus,
  { label: string; dot: string; pulse: boolean; text: string }
> = {
  idle: {
    label: "Ready",
    dot: "bg-zinc-400",
    pulse: false,
    text: "text-zinc-300",
  },
  listening: {
    label: "Listening...",
    dot: "bg-teal-400",
    pulse: true,
    text: "text-teal-300",
  },
  thinking: {
    label: "Thinking...",
    dot: "bg-purple-400",
    pulse: true,
    text: "text-purple-300",
  },
  speaking: {
    label: "Speaking...",
    dot: "bg-amber-400",
    pulse: true,
    text: "text-amber-300",
  },
};

export function StatusIndicator({ status, latencyMs }: StatusIndicatorProps) {
  const cfg = STATUS_CONFIG[status];
  return (
    <div className="flex items-center gap-3">
      <div
        className={cn(
          "inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 backdrop-blur",
          cfg.text,
        )}
      >
        <span className="relative flex h-2.5 w-2.5">
          {cfg.pulse && (
            <span
              className={cn(
                "absolute inline-flex h-full w-full animate-ping rounded-full opacity-75",
                cfg.dot,
              )}
            />
          )}
          <span
            className={cn(
              "relative inline-flex h-2.5 w-2.5 rounded-full",
              cfg.dot,
            )}
          />
        </span>
        <span className="text-xs font-medium tracking-wide">{cfg.label}</span>
      </div>

      {typeof latencyMs === "number" && latencyMs > 0 && (
        <div className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-1 text-[10px] font-mono uppercase tracking-wider text-emerald-300">
          {Math.round(latencyMs)}ms
        </div>
      )}
    </div>
  );
}
