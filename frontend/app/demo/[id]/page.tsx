import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { DemoWorkspace } from "@/components/DemoWorkspace";
import { fetchUseCase } from "@/lib/useCases";
import type { UseCaseMetadata } from "@/types/useCase";

export const dynamic = "force-dynamic";

interface DemoPageProps {
  params: Promise<{ id: string }>;
}

export default async function DemoPage({ params }: DemoPageProps) {
  const { id } = await params;
  let useCase: UseCaseMetadata | null = null;
  try {
    useCase = await fetchUseCase(id);
  } catch {
    notFound();
  }

  if (!useCase || useCase.id !== id) {
    notFound();
  }

  return (
    <main className="relative isolate min-h-dvh overflow-x-clip px-4 py-8 sm:px-8">
      <div
        className="pointer-events-none absolute inset-0 overflow-hidden"
        aria-hidden
      >
        <BackgroundOrbs />
      </div>

      <div className="relative z-10 mx-auto flex w-full max-w-7xl flex-col gap-6">
        <Link
          href="/"
          className="inline-flex w-fit items-center gap-2 text-xs text-zinc-400 transition hover:text-white"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          All demos
        </Link>

        <DemoWorkspace useCase={useCase} />
      </div>
    </main>
  );
}

function BackgroundOrbs() {
  return (
    <>
      <div className="pointer-events-none absolute -top-32 left-1/4 h-[480px] w-[480px] -translate-x-1/2 rounded-full bg-teal-500/10 blur-3xl" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[420px] w-[420px] translate-x-1/3 translate-y-1/3 rounded-full bg-purple-500/10 blur-3xl" />
    </>
  );
}
