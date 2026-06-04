import type { UseCaseMetadata } from "@/types/useCase";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchUseCases(): Promise<UseCaseMetadata[]> {
  const res = await fetch(`${API_BASE}/use_cases`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load use cases: ${res.status}`);
  const data = (await res.json()) as { use_cases: UseCaseMetadata[] };
  return data.use_cases;
}

export async function fetchUseCase(id: string): Promise<UseCaseMetadata> {
  const res = await fetch(`${API_BASE}/use_cases/${id}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Failed to load use case ${id}: ${res.status}`);
  return (await res.json()) as UseCaseMetadata;
}

/** Tailwind class snippets per accent (gradient + ring + hover). */
const TEAL_VOICE = {
  border: "border-teal-500/20",
  headerIcon: "text-teal-400",
  micIdle: "text-teal-300 shadow-[0_0_40px_rgba(45,212,191,0.3)] bg-teal-500/15",
  micListening:
    "text-teal-100 shadow-[0_0_80px_rgba(45,212,191,0.5)] bg-teal-500/25 scale-105",
  micGlow: "bg-teal-500/40",
  ripple: "border-teal-400/60",
  subtitle: "text-teal-400/80",
};

export const ACCENT_STYLES: Record<
  string,
  {
    badge: string;
    cardGlow: string;
    icon: string;
    button: string;
    ring: string;
    voice?: typeof TEAL_VOICE;
  }
> = {
  emerald: {
    badge: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
    cardGlow: "from-emerald-500/15 via-emerald-400/5 to-transparent",
    icon: "text-emerald-300 bg-emerald-500/15",
    button: "bg-emerald-500/90 hover:bg-emerald-400 text-emerald-950",
    ring: "ring-emerald-500/40",
    voice: {
      border: "border-emerald-500/20",
      headerIcon: "text-emerald-400",
      micIdle: "text-emerald-300 shadow-[0_0_40px_rgba(16,185,129,0.3)] bg-emerald-500/15",
      micListening: "text-emerald-100 shadow-[0_0_80px_rgba(16,185,129,0.5)] bg-emerald-500/25 scale-105",
      micGlow: "bg-emerald-500/40",
      ripple: "border-emerald-400/60",
      subtitle: "text-emerald-400/80",
    },
  },
  amber: {
    badge: "bg-amber-500/15 text-amber-300 border-amber-500/30",
    cardGlow: "from-amber-500/15 via-amber-400/5 to-transparent",
    icon: "text-amber-300 bg-amber-500/15",
    button: "bg-amber-500/90 hover:bg-amber-400 text-amber-950",
    ring: "ring-amber-500/40",
    voice: {
      border: "border-amber-500/20",
      headerIcon: "text-amber-400",
      micIdle: "text-amber-300 shadow-[0_0_40px_rgba(245,158,11,0.3)] bg-amber-500/15",
      micListening:
        "text-amber-100 shadow-[0_0_80px_rgba(245,158,11,0.5)] bg-amber-500/25 scale-105",
      micGlow: "bg-amber-500/40",
      ripple: "border-amber-400/60",
      subtitle: "text-amber-400/80",
    },
  },
  indigo: {
    badge: "bg-indigo-500/15 text-indigo-300 border-indigo-500/30",
    cardGlow: "from-indigo-500/15 via-indigo-400/5 to-transparent",
    icon: "text-indigo-300 bg-indigo-500/15",
    button: "bg-indigo-500/90 hover:bg-indigo-400 text-white",
    ring: "ring-indigo-500/40",
    voice: {
      border: "border-indigo-500/20",
      headerIcon: "text-indigo-400",
      micIdle: "text-indigo-300 shadow-[0_0_40px_rgba(99,102,241,0.3)] bg-indigo-500/15",
      micListening:
        "text-indigo-100 shadow-[0_0_80px_rgba(99,102,241,0.5)] bg-indigo-500/25 scale-105",
      micGlow: "bg-indigo-500/40",
      ripple: "border-indigo-400/60",
      subtitle: "text-indigo-400/80",
    },
  },
  cyan: {
    badge: "bg-cyan-500/15 text-cyan-300 border-cyan-500/30",
    cardGlow: "from-cyan-500/15 via-cyan-400/5 to-transparent",
    icon: "text-cyan-300 bg-cyan-500/15",
    button: "bg-cyan-500/90 hover:bg-cyan-400 text-cyan-950",
    ring: "ring-cyan-500/40",
    voice: {
      border: "border-cyan-500/20",
      headerIcon: "text-cyan-400",
      micIdle: "text-cyan-300 shadow-[0_0_40px_rgba(34,211,238,0.3)] bg-cyan-500/15",
      micListening:
        "text-cyan-100 shadow-[0_0_80px_rgba(34,211,238,0.5)] bg-cyan-500/25 scale-105",
      micGlow: "bg-cyan-500/40",
      ripple: "border-cyan-400/60",
      subtitle: "text-cyan-400/80",
    },
  },
  rose: {
    badge: "bg-rose-500/15 text-rose-300 border-rose-500/30",
    cardGlow: "from-rose-500/15 via-rose-400/5 to-transparent",
    icon: "text-rose-300 bg-rose-500/15",
    button: "bg-rose-500/90 hover:bg-rose-400 text-white",
    ring: "ring-rose-500/40",
    voice: {
      border: "border-rose-500/20",
      headerIcon: "text-rose-400",
      micIdle: "text-rose-300 shadow-[0_0_40px_rgba(244,63,94,0.3)] bg-rose-500/15",
      micListening:
        "text-rose-100 shadow-[0_0_80px_rgba(244,63,94,0.5)] bg-rose-500/25 scale-105",
      micGlow: "bg-rose-500/40",
      ripple: "border-rose-400/60",
      subtitle: "text-rose-400/80",
    },
  },
  sky: {
    badge: "bg-sky-500/15 text-sky-300 border-sky-500/30",
    cardGlow: "from-sky-500/15 via-sky-400/5 to-transparent",
    icon: "text-sky-300 bg-sky-500/15",
    button: "bg-sky-500/90 hover:bg-sky-400 text-sky-950",
    ring: "ring-sky-500/40",
    voice: {
      border: "border-sky-500/20",
      headerIcon: "text-sky-400",
      micIdle: "text-sky-300 shadow-[0_0_40px_rgba(14,165,233,0.3)] bg-sky-500/15",
      micListening:
        "text-sky-100 shadow-[0_0_80px_rgba(14,165,233,0.5)] bg-sky-500/25 scale-105",
      micGlow: "bg-sky-500/40",
      ripple: "border-sky-400/60",
      subtitle: "text-sky-400/80",
    },
  },
  orange: {
    badge: "bg-orange-500/15 text-orange-300 border-orange-500/30",
    cardGlow: "from-orange-500/15 via-orange-400/5 to-transparent",
    icon: "text-orange-300 bg-orange-500/15",
    button: "bg-orange-500/90 hover:bg-orange-400 text-orange-950",
    ring: "ring-orange-500/40",
    voice: {
      border: "border-orange-500/20",
      headerIcon: "text-orange-400",
      micIdle: "text-orange-300 shadow-[0_0_40px_rgba(249,115,22,0.3)] bg-orange-500/15",
      micListening:
        "text-orange-100 shadow-[0_0_80px_rgba(249,115,22,0.5)] bg-orange-500/25 scale-105",
      micGlow: "bg-orange-500/40",
      ripple: "border-orange-400/60",
      subtitle: "text-orange-400/80",
    },
  },
  violet: {
    badge: "bg-violet-500/15 text-violet-300 border-violet-500/30",
    cardGlow: "from-violet-500/15 via-violet-400/5 to-transparent",
    icon: "text-violet-300 bg-violet-500/15",
    button: "bg-violet-500/90 hover:bg-violet-400 text-white",
    ring: "ring-violet-500/40",
    voice: {
      border: "border-violet-500/20",
      headerIcon: "text-violet-400",
      micIdle: "text-violet-300 shadow-[0_0_40px_rgba(139,92,246,0.3)] bg-violet-500/15",
      micListening:
        "text-violet-100 shadow-[0_0_80px_rgba(139,92,246,0.5)] bg-violet-500/25 scale-105",
      micGlow: "bg-violet-500/40",
      ripple: "border-violet-400/60",
      subtitle: "text-violet-400/80",
    },
  },
  teal: {
    badge: "bg-teal-500/15 text-teal-300 border-teal-500/30",
    cardGlow: "from-teal-500/15 via-teal-400/5 to-transparent",
    icon: "text-teal-300 bg-teal-500/15",
    button: "bg-teal-500/90 hover:bg-teal-400 text-teal-950",
    ring: "ring-teal-500/40",
    voice: TEAL_VOICE,
  },
};

export function accentStyles(accent: string) {
  const s = ACCENT_STYLES[accent] ?? ACCENT_STYLES.teal;
  return { ...s, voice: s.voice ?? TEAL_VOICE };
}
