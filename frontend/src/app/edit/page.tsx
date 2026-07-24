"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  api,
  type EditProject,
  type EditSummary,
  type EditWorkspace,
} from "@/lib/api";
import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";
import { SiteHeader } from "@/components/SiteHeader";

export default function EditHubPage() {
  const [summary, setSummary] = useState<EditSummary | null>(null);
  const [workspaces, setWorkspaces] = useState<EditWorkspace[]>([]);
  const [projects, setProjects] = useState<EditProject[]>([]);
  const [workspaceId, setWorkspaceId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [seeding, setSeeding] = useState(false);

  const refresh = async () => {
    setLoading(true);
    setError(null);
    try {
      const [s, ws] = await Promise.all([api.editSummary(), api.editListWorkspaces()]);
      setSummary(s);
      setWorkspaces(ws);
      const active = workspaceId && ws.some((w) => w.id === workspaceId) ? workspaceId : ws[0]?.id ?? null;
      setWorkspaceId(active);
      if (active) {
        setProjects(await api.editListProjects(active));
      } else {
        setProjects([]);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load Edit");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const seedInternal = async () => {
    setSeeding(true);
    setError(null);
    try {
      const ws = await api.editSeedInternal();
      setWorkspaceId(ws.id);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Seed failed");
    } finally {
      setSeeding(false);
    }
  };

  return (
    <main className="min-h-screen pb-20">
      <SiteHeader />
      <div className="ac-container pt-10 md:pt-14">
        <PageHeader
          eyebrow="Art City Edit"
          title="Edit and repurpose long-form footage"
          description="Transform interviews and programmes into branded multi-ratio social clips — guided by a prompt, approved by people, governed by Art City."
          actions={
            <>
              <Link href="/edit/apply" className="ac-btn">
                Request access
              </Link>
              <Link href="/edit/admin" className="ac-btn">
                Admin
              </Link>
            </>
          }
        />

        <div className="mb-12 grid gap-4 md:grid-cols-3 animate-rise-delay">
          {[
            ["Editorial intelligence", "Candidates with scores, explanations, and risk flags"],
            ["Brand memory", "Profiles for captions, tone, and compliance"],
            ["Governed access", "Art City approval before processing entitlements"],
          ].map(([t, d]) => (
            <div key={t} className="border border-[var(--line)] bg-[rgba(10,15,22,0.4)] p-5">
              <p className="ac-display text-[var(--gold-bright)]">{t}</p>
              <p className="mt-2 text-sm text-[var(--mist)]">{d}</p>
            </div>
          ))}
        </div>

        {summary ? (
          <p className="mb-8 text-[0.72rem] tracking-[0.16em] text-[var(--mist-soft)] uppercase">
            Workspaces {summary.workspaces} · Projects {summary.projects} · Pending apps{" "}
            {summary.pending_applications}
          </p>
        ) : null}

        {loading ? (
          <p className="text-[0.8rem] tracking-[0.18em] text-[var(--mist)] uppercase">
            Opening Edit…
          </p>
        ) : error ? (
          <p className="text-[var(--danger)]">{error}</p>
        ) : workspaces.length === 0 ? (
          <EmptyState
            title="No Edit workspace yet"
            description="Seed the internal Art City Edit workspace (admins) or submit an access application."
            action={
              <button
                type="button"
                className="ac-btn ac-btn-primary"
                disabled={seeding}
                onClick={() => void seedInternal()}
              >
                {seeding ? "Seeding…" : "Seed internal workspace"}
              </button>
            }
          />
        ) : (
          <>
            <div className="mb-6 flex flex-wrap items-center gap-3">
              <label className="text-[0.72rem] tracking-[0.14em] text-[var(--mist)] uppercase">
                Workspace
              </label>
              <select
                className="ac-input max-w-md"
                value={workspaceId ?? ""}
                onChange={(e) => {
                  const id = e.target.value;
                  setWorkspaceId(id);
                  void api.editListProjects(id).then(setProjects).catch((err) => {
                    setError(err instanceof Error ? err.message : "Failed");
                  });
                }}
              >
                {workspaces.map((w) => (
                  <option key={w.id} value={w.id}>
                    {w.name} ({w.status})
                  </option>
                ))}
              </select>
              {workspaceId ? (
                <Link href={`/edit/workspace/${workspaceId}`} className="ac-btn ac-btn-primary">
                  Open workspace
                </Link>
              ) : null}
            </div>

            {projects.length === 0 ? (
              <EmptyState
                title="No Edit projects"
                description="Open a workspace to upload long-form video and create a project."
                action={
                  workspaceId ? (
                    <Link
                      href={`/edit/workspace/${workspaceId}`}
                      className="ac-btn ac-btn-primary"
                    >
                      Create project
                    </Link>
                  ) : null
                }
              />
            ) : (
              <ul className="border-t border-[var(--line)]">
                {projects.map((p, i) => (
                  <li key={p.id} className="ac-row">
                    <Link
                      href={`/edit/${p.id}`}
                      className="group grid grid-cols-[auto_1fr_auto] items-baseline gap-4 py-7 md:gap-8"
                    >
                      <span className="ac-display w-8 text-[0.75rem] tracking-[0.14em] text-[var(--mist-soft)]">
                        {String(i + 1).padStart(2, "0")}
                      </span>
                      <div>
                        <p className="ac-display text-2xl tracking-tight transition group-hover:text-[var(--gold-bright)]">
                          {p.title}
                        </p>
                        <p className="mt-2 text-[0.72rem] tracking-[0.16em] text-[var(--mist-soft)] uppercase">
                          {p.status.replaceAll("_", " ")}
                        </p>
                      </div>
                      <span className="text-[0.72rem] tracking-[0.14em] text-[var(--mist)] uppercase">
                        Open
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </div>
    </main>
  );
}
