"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type Project } from "@/lib/api";
import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";
import { SiteHeader } from "@/components/SiteHeader";

export default function PublishHubPage() {
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
          eyebrow="Art City delivery"
          title="Publish"
          description="Approve → package → export masters. Broadcast 16:9, vertical 9:16, square 1:1, stems, checksums, and delivery checklist."
        />

        <div className="mb-12 grid gap-4 md:grid-cols-4 animate-rise-delay">
          {[
            ["01", "Select cinema package"],
            ["02", "Package masters"],
            ["03", "Pass checklist"],
            ["04", "Release to channel"],
          ].map(([n, t]) => (
            <div key={n} className="border border-[var(--line)] bg-[rgba(10,15,22,0.4)] p-4">
              <p className="ac-display text-[0.68rem] tracking-[0.2em] text-[var(--gold)]">{n}</p>
              <p className="mt-2 text-sm text-[var(--paper-dim)]">{t}</p>
            </div>
          ))}
        </div>

        {loading ? (
          <p className="text-[0.8rem] tracking-[0.18em] text-[var(--mist)] uppercase">
            Loading projects…
          </p>
        ) : error ? (
          <p className="text-[var(--danger)]">{error}</p>
        ) : projects.length === 0 ? (
          <EmptyState
            title="Nothing to publish"
            description="Create a project and cinema package first, then open Publish for delivery."
            action={
              <Link href="/cinema" className="ac-btn ac-btn-primary">
                Open cinema
              </Link>
            }
          />
        ) : (
          <ul className="border-t border-[var(--line)]">
            {projects.map((p, i) => (
              <li key={p.id} className="ac-row">
                <Link
                  href={`/publish/${p.id}`}
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
                      Masters · Checklist · Channel release
                    </p>
                  </div>
                  <span className="ac-display text-[0.68rem] tracking-[0.18em] text-[var(--gold)] uppercase">
                    Publish →
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
