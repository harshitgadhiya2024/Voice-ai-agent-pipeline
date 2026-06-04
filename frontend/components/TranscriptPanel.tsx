"use client";

import { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";

interface TranscriptPanelProps {
  userTranscript: string;
  botReply: string;
  isBotStreaming: boolean;
}

export function TranscriptPanel({
  userTranscript,
  botReply,
  isBotStreaming,
}: TranscriptPanelProps) {
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [userTranscript, botReply]);

  const hasContent = !!(userTranscript || botReply);

  return (
    <div
      ref={scrollRef}
      className={cn(
        "w-full rounded-xl border border-white/10 bg-zinc-900/40 p-4 text-sm leading-relaxed backdrop-blur",
        !hasContent && "flex min-h-[120px] items-center justify-center",
      )}
    >
      {!hasContent ? (
        <span className="text-zinc-500">
          Say something — your transcript will appear here.
        </span>
      ) : (
        <div className="space-y-4">
          {userTranscript && (
            <div>
              <span className="mr-2 inline-block rounded-md bg-teal-500/15 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-teal-300">
                You
              </span>
              <span className="text-zinc-100">{userTranscript}</span>
            </div>
          )}
          {botReply && (
            <div>
              <span className="mr-2 inline-block rounded-md bg-purple-500/15 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-purple-300">
                Bot
              </span>
              <span className="text-zinc-100">{botReply}</span>
              {isBotStreaming && (
                <span className="ml-0.5 inline-block h-4 w-[2px] animate-pulse bg-purple-300 align-middle" />
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
