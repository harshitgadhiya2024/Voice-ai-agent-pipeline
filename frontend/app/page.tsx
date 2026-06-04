import { UseCaseGallery } from "@/components/UseCaseGallery";
import { fetchUseCases } from "@/lib/useCases";
import type { UseCaseMetadata } from "@/types/useCase";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  let useCases: UseCaseMetadata[] = [];
  let loadError: string | null = null;
  try {
    useCases = await fetchUseCases();
  } catch (e) {
    loadError =
      e instanceof Error
        ? e.message
        : "Could not reach the backend. Start it from backend/ with conda run -n base uvicorn main:app --reload.";
  }

  return (
    <main className="relative isolate flex min-h-dvh flex-col overflow-x-clip px-4 py-12 sm:px-8">
      <div
        className="pointer-events-none absolute inset-0 overflow-hidden"
        aria-hidden
      >
        <BackgroundOrbs />
      </div>

      <header className="relative z-10 mx-auto flex w-full max-w-6xl flex-col gap-3 text-center">
        <span className="mx-auto rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.2em] text-teal-300">
          1,500+ knowledge · 9 verticals · LangGraph
        </span>
        <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
          Production-grade Voice AI demos
        </h1>
        <p className="mx-auto max-w-2xl text-sm leading-relaxed text-zinc-400 sm:text-base">
          Nine industry demos — each with 1,000+ structured knowledge records
          across 20 cities, agentic intent routing, voice-only
          UI, and multi-language STT/TTS (English / Hindi / Gujarati).
        </p>
      </header>

      <section className="relative z-10 mx-auto mt-12 w-full max-w-6xl">
        {loadError ? (
          <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 p-6 text-sm text-rose-200">
            <p className="font-semibold">Backend unreachable</p>
            <p className="mt-1 text-rose-300/80">{loadError}</p>
            <pre className="mt-3 overflow-x-auto rounded-lg bg-black/40 p-3 text-[12px] text-rose-100">
              cd backend && conda run -n base uvicorn main:app --reload
            </pre>
          </div>
        ) : (
          <UseCaseGallery useCases={useCases} />
        )}
      </section>

      <footer className="relative z-10 mx-auto mt-16 max-w-6xl text-center text-[11px] text-zinc-600">
        Built with Next.js · FastAPI · LangGraph · Sarvam · Groq
      </footer>
    </main>
  );
}

function BackgroundOrbs() {
  return (
    <>
      <div className="pointer-events-none absolute -top-40 left-1/2 h-[520px] w-[520px] -translate-x-1/2 rounded-full bg-teal-500/10 blur-3xl" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[420px] w-[420px] translate-x-1/3 translate-y-1/3 rounded-full bg-purple-500/10 blur-3xl" />
      <div className="pointer-events-none absolute bottom-1/4 left-0 h-[300px] w-[300px] -translate-x-1/3 rounded-full bg-amber-500/5 blur-3xl" />
    </>
  );
}
