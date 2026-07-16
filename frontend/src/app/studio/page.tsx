"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type Project } from "@/lib/api";
import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";
import { SiteHeader } from "@/components/SiteHeader";

export default function StudioHubPage() {
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
          eyebrow="Art City Studio"
          title="Individual production assets"
          description="Create single images, videos, voice tracks, music tracks, or scene/shot takes — then review. For full campaigns, use Art City Cinema."
        />

        {loading ? (
          <p className="text-[0.8rem] tracking-[0.18em] text-[var(--mist)] uppercase">Opening floor…</p>
        ) : error ? (
          <p className="text-[var(--danger)]">{error}</p>
        ) : projects.length === 0 ? (
          <EmptyState
            title="No productions on the floor"
            description="Create a project first, then open the media studio for video, voice, and sound."
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
                  href={`/studio/${p.id}`}
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
                      Video · Voice · Music · Image · Review
                    </p>
                  </div>
                  <span className="ac-display text-[0.68rem] tracking-[0.18em] text-[var(--gold)] uppercase">
                    Enter →
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
