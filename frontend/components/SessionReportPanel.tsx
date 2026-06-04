"use client";

import { FileText, X } from "lucide-react";
import type { SessionReport } from "@/types";

interface SessionReportPanelProps {
  report: SessionReport | null;
  onClose: () => void;
}

export function SessionReportPanel({
  report,
  onClose,
}: SessionReportPanelProps) {
  if (!report) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/60 p-4 sm:items-center">
      <div className="max-h-[85vh] w-full max-w-lg overflow-hidden rounded-2xl border border-white/10 bg-zinc-900 shadow-2xl">
        <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
          <div className="flex items-center gap-2 text-sm font-semibold text-teal-200">
            <FileText className="h-4 w-4" />
            Session report
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1 text-zinc-400 hover:bg-white/10 hover:text-white"
            aria-label="Close report"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="space-y-4 overflow-y-auto p-4 text-sm text-zinc-300">
          <div>
            <p className="text-[10px] uppercase tracking-wider text-zinc-500">
              College
            </p>
            <p className="font-medium text-white">{report.college_name}</p>
          </div>
          {report.summary && (
            <div>
              <p className="text-[10px] uppercase tracking-wider text-zinc-500">
                Summary
              </p>
              <p>{report.summary}</p>
            </div>
          )}
          <div>
            <p className="text-[10px] uppercase tracking-wider text-zinc-500">
              Primary intent
            </p>
            <p className="capitalize">{report.primary_intent}</p>
          </div>
          {report.entities.length > 0 && (
            <div>
              <p className="mb-2 text-[10px] uppercase tracking-wider text-zinc-500">
                Extracted entities
              </p>
              <ul className="space-y-1">
                {report.entities.map((e, i) => (
                  <li
                    key={`${e.type}-${i}`}
                    className="rounded-lg bg-white/5 px-2 py-1 text-xs"
                  >
                    <span className="text-teal-300">{e.type}</span>: {e.value}
                    {e.confidence != null && (
                      <span className="ml-1 text-zinc-500">
                        ({Math.round(e.confidence * 100)}%)
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {Object.keys(report.slots || {}).length > 0 && (
            <div>
              <p className="mb-2 text-[10px] uppercase tracking-wider text-zinc-500">
                Collected details
              </p>
              <pre className="overflow-x-auto rounded-lg bg-black/30 p-2 text-[11px] text-zinc-400">
                {JSON.stringify(report.slots, null, 2)}
              </pre>
            </div>
          )}
          <div>
            <p className="mb-2 text-[10px] uppercase tracking-wider text-zinc-500">
              Conversation ({report.turn_count} user turns)
            </p>
            <div className="max-h-48 space-y-2 overflow-y-auto rounded-lg border border-white/5 p-2">
              {report.conversation.map((m, i) => (
                <p
                  key={i}
                  className={
                    m.role === "user"
                      ? "text-teal-200/90"
                      : "text-zinc-400"
                  }
                >
                  <span className="font-medium capitalize">{m.role}: </span>
                  {m.content}
                </p>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
