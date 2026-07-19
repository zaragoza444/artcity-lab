"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type Project } from "@/lib/api";
import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";
import { SiteHeader } from "@/components/SiteHeader";

export default function AdvertisingHubPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listProjects()
      .then(setProjects)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="min-h-screen pb-20">
      <SiteHeader />
      <div className="ac-container pt-10 md:pt-14">
        <PageHeader
          eyebrow="Art City Advertising"
          title="AI media campaigns for cinema & social"
          description="Model Gateway builds broadcast, vertical, and square films with music, voice-over, end card, cultural KB enrichment, technical QC, and Publish-ready ZIP masters."
        />

        <div className="mb-12 grid gap-4 md:grid-cols-4 animate-rise-delay">
          {[
            ["Video", "16:9 · 9:16 · 1:1 cutdowns"],
            ["Audio", "Music bed · SFX · stems"],
            ["Voice", "Dialect-aware VO takes"],
            ["Cinema", "Manifest · QC · ZIP · Publish"],
          ].map(([t, d]) => (
            <div key={t} className="border border-[var(--line)] bg-[rgba(10,15,22,0.4)] p-5">
              <p className="ac-display text-[var(--gold-bright)]">{t}</p>
              <p className="ac-serif mt-2 text-sm text-[var(--mist)]">{d}</p>
            </div>
          ))}
        </div>

        <div className="mb-8 flex flex-wrap gap-3">
          <Link href="/cinema" className="ac-btn ac-btn-primary">
            Open Cinema floor
          </Link>
          <Link href="/studio" className="ac-btn ac-btn-secondary">
            Studio singles
          </Link>
          <Link href="/publish" className="ac-btn ac-btn-ghost">
            Publish masters
          </Link>
        </div>

        {loading ? (
          <p className="text-[var(--mist)]">Loading projects…</p>
        ) : error ? (
          <p className="text-[var(--danger)]">{error}</p>
        ) : projects.length === 0 ? (
          <EmptyState
            title="No projects yet"
            description="Create a project, then render a full advertising package in Cinema."
            action={
              <Link href="/projects" className="ac-btn ac-btn-primary">
                Projects
              </Link>
            }
          />
        ) : (
          <ul className="grid gap-3 md:grid-cols-2">
            {projects.map((p) => (
              <li key={p.id}>
                <Link
                  href={`/cinema/${p.id}`}
                  className="block border border-[var(--line)] px-5 py-5 transition hover:border-[var(--gold)]"
                >
                  <p className="ac-display text-lg text-[var(--paper)]">{p.name}</p>
                  <p className="mt-1 text-sm text-[var(--mist)]">
                    Render advertising campaign → Cinema
                  </p>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </main>
  );
}
