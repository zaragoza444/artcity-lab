"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type Project } from "@/lib/api";
import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";
import { SiteHeader } from "@/components/SiteHeader";

export default function CinemaHubPage() {
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
          eyebrow="Art City Cinema"
          title="Complete advertising campaigns"
          description="Hero film, social adaptations, music, voice-over, end card, campaign manifest, technical QC, and downloadable ZIP — not single assets."
        />

        <div className="mb-12 grid gap-4 md:grid-cols-3 animate-rise-delay">
          {[
            ["Campaign outputs", "Hero · 9:16 · 1:1 · music · VO · end card"],
            ["Technical QC", "Duration · aspect · loudness · SHA-256"],
            ["Delivery", "Manifest · validation JSON · ZIP package"],
          ].map(([t, d]) => (
            <div key={t} className="border border-[var(--line)] bg-[rgba(10,15,22,0.4)] p-5">
              <p className="ac-display text-[var(--gold-bright)]">{t}</p>
              <p className="mt-2 text-sm text-[var(--mist)]">{d}</p>
            </div>
          ))}
        </div>

        {loading ? (
          <p className="text-[0.8rem] tracking-[0.18em] text-[var(--mist)] uppercase">
            Loading productions…
          </p>
        ) : error ? (
          <p className="text-[var(--danger)]">{error}</p>
        ) : projects.length === 0 ? (
          <EmptyState
            title="No campaigns ready"
            description="Create a project, then open Cinema to render a full advertising package."
            action={
              <Link href="/projects" className="ac-btn ac-btn-primary">
                Create project
              </Link>
            }
          />
        ) : (
          <ul className="border-t border-[var(--line)]">
            {projects.map((p, i) => (
              <li key={p.id} className="ac-row">
                <Link
                  href={`/cinema/${p.id}`}
                  className="group grid grid-cols-[auto_1fr_auto] items-baseline gap-4 py-7 md:gap-8"
                >
                  <span className="ac-display w-8 text-[0.75rem] tracking-[0.14em] text-[var(--mist-soft)]">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <div>
                    <p className="ac-display text-2xl tracking-tight transition group-hover:text-[var(--gold-bright)]">
                      {p.name}
                    </p>
                    <p className="mt-2 text-[0.72rem] tracking-[0.16em] text-[var(--mist-soft)] uppercase">
                      Cinema · Advertising · Music · Cutdowns
                    </p>
                  </div>
                  <span className="ac-display text-[0.68rem] tracking-[0.18em] text-[var(--gold)] uppercase">
                    Render →
                  </span>
                </Link>
                <div className="ac-rule" />
              </li>
            ))}
          </ul>
        )}
      </div>
    </main>
  );
}
