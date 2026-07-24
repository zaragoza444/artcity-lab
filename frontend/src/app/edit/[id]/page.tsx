"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import {
  api,
  type EditCandidate,
  type EditProject,
  type EditRenderJob,
  type EditTimelineVersion,
} from "@/lib/api";
import { PageHeader } from "@/components/PageHeader";
import { SiteHeader } from "@/components/SiteHeader";

export default function EditProjectWorkspacePage() {
  const params = useParams();
  const projectId = String(params.id);
  const [project, setProject] = useState<EditProject | null>(null);
  const [candidates, setCandidates] = useState<EditCandidate[]>([]);
  const [timelines, setTimelines] = useState<EditTimelineVersion[]>([]);
  const [renders, setRenders] = useState<EditRenderJob[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [packageJson, setPackageJson] = useState<Record<string, unknown> | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [p, c, t, r] = await Promise.all([
        api.editGetProject(projectId),
        api.editListCandidates(projectId),
        api.editListTimelines(projectId),
        api.editListRenders(projectId),
      ]);
      setProject(p);
      setCandidates(c);
      setTimelines(t);
      setRenders(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load project");
    }
  }, [projectId]);

  useEffect(() => {
    void refresh();
    const timer = setInterval(() => void refresh(), 4000);
    return () => clearInterval(timer);
  }, [refresh]);

  const run = async (fn: () => Promise<void>) => {
    setBusy(true);
    setError(null);
    try {
      await fn();
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Action failed");
    } finally {
      setBusy(false);
    }
  };

  const toggle = (id: string) => {
    setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  };

  return (
    <main className="min-h-screen pb-20">
      <SiteHeader />
      <div className="ac-container pt-10 md:pt-14">
        <PageHeader
          eyebrow="Art City Edit"
          title={project?.title ?? "Edit project"}
          description={`Status: ${project?.status?.replaceAll("_", " ") ?? "…"} — analyse, pin candidates, build a timeline, render multi-ratio packages.`}
          actions={
            <Link href="/edit" className="ac-btn">
              Hub
            </Link>
          }
        />

        {error ? <p className="mb-4 text-[var(--danger)]">{error}</p> : null}

        <div className="mb-8 flex flex-wrap gap-3">
          <button
            type="button"
            className="ac-btn ac-btn-primary"
            disabled={busy}
            onClick={() => void run(async () => { await api.editStartAnalysis(projectId); })}
          >
            Run analysis
          </button>
          <button
            type="button"
            className="ac-btn"
            disabled={busy || selected.length === 0}
            onClick={() =>
              void run(async () => {
                await api.editCreateTimeline(projectId, selected, "First cut");
              })
            }
          >
            Build timeline from pinned
          </button>
        </div>

        <section className="mb-12">
          <h2 className="ac-display mb-4 text-xl">Candidate clips</h2>
          {candidates.length === 0 ? (
            <p className="text-sm text-[var(--mist)]">
              No candidates yet. Run analysis (worker processes the queue).
            </p>
          ) : (
            <ul className="space-y-3">
              {candidates.map((c) => (
                <li
                  key={c.id}
                  className="border border-[var(--line)] bg-[rgba(10,15,22,0.35)] p-4"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="ac-display text-[var(--gold-bright)]">
                        {c.source_in.toFixed(1)}s – {c.source_out.toFixed(1)}s · score{" "}
                        {c.score.toFixed(2)}
                      </p>
                      <p className="mt-2 text-sm text-[var(--mist)]">{c.explanation}</p>
                      {c.risks_json && c.risks_json.length > 0 ? (
                        <p className="mt-1 text-xs text-[var(--danger)]">
                          Risks: {JSON.stringify(c.risks_json)}
                        </p>
                      ) : null}
                    </div>
                    <div className="flex gap-2">
                      <button
                        type="button"
                        className={`ac-btn ${selected.includes(c.id) || c.user_decision === "pin" ? "ac-btn-primary" : ""}`}
                        disabled={busy}
                        onClick={() =>
                          void run(async () => {
                            await api.editCandidateDecision(c.id, "pin");
                            toggle(c.id);
                          })
                        }
                      >
                        Pin
                      </button>
                      <button
                        type="button"
                        className="ac-btn"
                        disabled={busy}
                        onClick={() =>
                          void run(async () => {
                            await api.editCandidateDecision(c.id, "reject");
                          })
                        }
                      >
                        Reject
                      </button>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="mb-12">
          <h2 className="ac-display mb-4 text-xl">Timeline versions</h2>
          <ul className="space-y-3">
            {timelines.map((t) => (
              <li key={t.id} className="border border-[var(--line)] p-4">
                <p className="ac-display">
                  v{t.version_number} {t.name ?? ""} · {t.status}
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  <button
                    type="button"
                    className="ac-btn"
                    disabled={busy}
                    onClick={() =>
                      void run(async () => {
                        await api.editSubmitTimelineReview(t.id);
                      })
                    }
                  >
                    Submit review
                  </button>
                  <button
                    type="button"
                    className="ac-btn"
                    disabled={busy}
                    onClick={() =>
                      void run(async () => {
                        await api.editDecideTimeline(t.id, "approve", "Approved for export");
                      })
                    }
                  >
                    Approve
                  </button>
                  <button
                    type="button"
                    className="ac-btn ac-btn-primary"
                    disabled={busy}
                    onClick={() =>
                      void run(async () => {
                        await api.editStartRender(projectId, t.id);
                      })
                    }
                  >
                    Render 9:16 / 16:9 / 4:5 / 1:1
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </section>

        <section>
          <h2 className="ac-display mb-4 text-xl">Renders & export</h2>
          <ul className="space-y-3">
            {renders.map((r) => (
              <li key={r.id} className="border border-[var(--line)] p-4">
                <p className="ac-display">
                  {r.state} · {r.preset} · ${r.cost_usd.toFixed(2)}
                </p>
                <button
                  type="button"
                  className="ac-btn mt-3"
                  disabled={busy}
                  onClick={() =>
                    void run(async () => {
                      setPackageJson(await api.editExportPackage(r.id));
                    })
                  }
                >
                  View package / QC
                </button>
              </li>
            ))}
          </ul>
          {packageJson ? (
            <pre className="mt-4 overflow-auto border border-[var(--line)] p-4 text-xs text-[var(--mist)]">
              {JSON.stringify(packageJson, null, 2)}
            </pre>
          ) : null}
        </section>
      </div>
    </main>
  );
}
