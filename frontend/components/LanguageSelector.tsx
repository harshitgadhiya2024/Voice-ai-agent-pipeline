"use client";

import { useEffect, useRef, useState } from "react";
import { ChevronDown, Globe } from "lucide-react";
import { cn } from "@/lib/utils";
import { LANGUAGE_OPTIONS, type Language } from "@/types";

interface LanguageSelectorProps {
  value: Language;
  onChange: (lang: Language) => void;
  disabled?: boolean;
}

export function LanguageSelector({
  value,
  onChange,
  disabled,
}: LanguageSelectorProps) {
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

  const current =
    LANGUAGE_OPTIONS.find((o) => o.code === value) || LANGUAGE_OPTIONS[0];

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        disabled={disabled}
        onClick={() => setOpen((v) => !v)}
        className={cn(
          "inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-zinc-200 transition hover:bg-white/10 backdrop-blur",
          disabled && "opacity-50 cursor-not-allowed",
        )}
      >
        <Globe className="h-3.5 w-3.5 text-teal-300" />
        <span>{current.native}</span>
        <ChevronDown
          className={cn(
            "h-3.5 w-3.5 text-zinc-400 transition",
            open && "rotate-180",
          )}
        />
      </button>

      {open && (
        <div className="absolute right-0 z-30 mt-2 w-44 overflow-hidden rounded-xl border border-white/10 bg-zinc-900/95 shadow-xl shadow-black/40 backdrop-blur-xl">
          {LANGUAGE_OPTIONS.map((opt) => {
            const active = opt.code === value;
            return (
              <button
                key={opt.code}
                onClick={() => {
                  onChange(opt.code);
                  setOpen(false);
                }}
                className={cn(
                  "flex w-full items-center justify-between px-3 py-2 text-left text-xs transition",
                  active
                    ? "bg-teal-500/15 text-teal-200"
                    : "text-zinc-200 hover:bg-white/5",
                )}
              >
                <span className="flex items-center gap-2">
                  <span>{opt.flag}</span>
                  <span className="font-medium">{opt.native}</span>
                </span>
                <span className="text-[10px] uppercase tracking-wider text-zinc-500">
                  {opt.code}
                </span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
