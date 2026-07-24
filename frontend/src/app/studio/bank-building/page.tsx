"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import {
  api,
  mediaAbsolute,
  withAccessToken,
  type GenerationJob,
} from "@/lib/api";
import { PageHeader } from "@/components/PageHeader";
import { SiteHeader } from "@/components/SiteHeader";

export default function BankBuildingImagePage() {
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [job, setJob] = useState<GenerationJob | null>(null);

  async function onGenerate(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const result = await api.generateBankBuilding({
        notes: notes.trim() || undefined,
        prefer_external: true,
      });
      setJob(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed");
    } finally {
      setBusy(false);
    }
  }

  const media = withAccessToken(mediaAbsolute(job?.media_url) || "");

  return (
    <main className="min-h-screen pb-20">
      <SiteHeader />
      <div className="ac-container pt-10 md:pt-14">
        <PageHeader
          eyebrow="Art City Studio · Image test"
          title="Bank building generate"
          description="Frontend + backend Studio path that generates a cinematic bank building still, then shows the production image."
        />

        <p className="mb-8">
          <Link
            href="/studio"
            className="text-[0.72rem] uppercase tracking-[0.16em] text-[var(--gold)] hover:text-[var(--gold-bright)]"
          >
            ← Studio floor
          </Link>
        </p>

        <form onSubmit={onGenerate} className="max-w-xl space-y-5">
          <label className="block space-y-2">
            <span className="ac-display text-[0.68rem] tracking-[0.18em] text-[var(--mist)] uppercase">
              Extra direction (optional)
            </span>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              placeholder="e.g. night rain, glass atrium reflection, Art City plaza"
              className="w-full border border-[var(--line)] bg-[rgba(10,15,22,0.55)] px-3 py-3 text-sm text-[var(--paper)] outline-none focus:border-[var(--gold)]"
            />
          </label>
          <button type="submit" disabled={busy} className="ac-btn ac-btn-primary">
            {busy ? "Generating…" : "Generate bank building image"}
          </button>
        </form>

        {error ? <p className="mt-6 text-[var(--danger)]">{error}</p> : null}

        {job ? (
          <section className="mt-12 max-w-3xl space-y-4">
            <div className="flex flex-wrap items-baseline gap-4 text-[0.72rem] uppercase tracking-[0.14em] text-[var(--mist)]">
              <span>Status · {job.status}</span>
              <span>Provider · {job.provider}</span>
              {job.provider_job_id ? <span>Job · {job.provider_job_id}</span> : null}
            </div>
            {media ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={media}
                alt={job.prompt || "Bank building"}
                className="w-full border border-[var(--line)] bg-black object-cover aspect-video"
              />
            ) : (
              <p className="text-sm text-[var(--mist)]">No media URL on job.</p>
            )}
            <p className="text-sm text-[var(--mist-soft)]">{job.prompt}</p>
            <Link
              href={`/studio/${job.project_id}`}
              className="inline-block text-[0.72rem] uppercase tracking-[0.16em] text-[var(--gold)]"
            >
              Open project studio →
            </Link>
          </section>
        ) : null}
      </div>
    </main>
  );
}
