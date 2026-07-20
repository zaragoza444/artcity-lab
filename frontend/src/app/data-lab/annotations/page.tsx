"use client";

import Link from "next/link";
import { FormEvent, Suspense, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { CoreShell } from "@/components/CoreShell";
import {
  api,
  type AnnotationStats,
  type AnnotationTask,
  type Dataset,
} from "@/lib/api";

type EditState = {
  text: string;
  dialect: string;
  translation: string;
  speaker: string;
  consent: boolean;
  comment: string;
};

function AnnotationsWorkspace() {
  const search = useSearchParams();
  const initialDataset = search.get("dataset") || "";

  const [tasks, setTasks] = useState<AnnotationTask[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [stats, setStats] = useState<AnnotationStats | null>(null);
  const [datasetId, setDatasetId] = useState(initialDataset);
  const [filterStatus, setFilterStatus] = useState("");
  const [filterMedia, setFilterMedia] = useState("");
  const [text, setText] = useState("");
  const [dialect, setDialect] = useState("sorani");
  const [translation, setTranslation] = useState("");
  const [mediaType, setMediaType] = useState("speech");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [edits, setEdits] = useState<Record<string, EditState>>({});

  const datasetName = useMemo(() => {
    const map = Object.fromEntries(datasets.map((d) => [d.id, d.name]));
    return (id: string) => map[id] || id.slice(0, 8);
  }, [datasets]);

  function load() {
    Promise.all([
      api.listAnnotations({
        dataset_id: datasetId || undefined,
        status: filterStatus || undefined,
        media_type: filterMedia || undefined,
      }),
      api.listDatasets(),
      api.annotationStats(datasetId || undefined),
    ])
      .then(([a, d, s]) => {
        setTasks(a);
        setDatasets(d);
        setStats(s);
        if (!datasetId && d[0]) setDatasetId(d[0].id);
        const next: Record<string, EditState> = {};
        for (const t of a) {
          const labels = (t.labels || {}) as {
            dialect?: string;
            translation?: string;
            speaker?: string;
            consent?: boolean;
          };
          const payload = t.payload as { text?: string };
          next[t.id] = {
            text: payload.text || "",
            dialect: labels.dialect || "sorani",
            translation: labels.translation || "",
            speaker: labels.speaker || "speaker_1",
            consent: Boolean(labels.consent),
            comment: "",
          };
        }
        setEdits(next);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Load failed"));
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [datasetId, filterStatus, filterMedia]);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    if (!datasetId || !text.trim()) return;
    setBusy(true);
    setError(null);
    try {
      await api.createAnnotation({
        dataset_id: datasetId,
        media_type: mediaType,
        payload: { text: text.trim(), language: "ku" },
        labels: {
          dialect,
          translation: translation.trim() || null,
          source: "manual",
          speaker: "speaker_1",
          consent: false,
        },
      });
      setText("");
      setTranslation("");
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Create failed");
    } finally {
      setBusy(false);
    }
  }

  async function saveReview(task: AnnotationTask, status: string) {
    const edit = edits[task.id];
    if (!edit) return;
    if (status === "rejected" && !edit.comment.trim()) {
      setError("Comment required to reject");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await api.updateAnnotation(task.id, {
        payload: { text: edit.text, language: "ku" },
        labels: {
          ...(task.labels || {}),
          dialect: edit.dialect,
          translation: edit.translation.trim() || null,
          speaker: edit.speaker,
          consent: edit.consent,
        },
        status,
        comment:
          edit.comment.trim() ||
          (status === "approved"
            ? "Approved in Annotations workspace"
            : status === "in_review"
              ? "Moved to review"
              : status === "conflict"
                ? "Marked conflict"
                : "Updated"),
      });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Update failed");
    } finally {
      setBusy(false);
    }
  }

  function patchEdit(id: string, patch: Partial<EditState>) {
    setEdits((prev) => ({ ...prev, [id]: { ...prev[id], ...patch } }));
  }

  return (
    <>
      <div className="mb-6 flex flex-wrap gap-3">
        <Link
          href="/data-lab"
          className="border border-[var(--line)] px-4 py-2 text-xs uppercase tracking-[0.14em] text-[var(--paper-dim)]"
        >
          Data Lab
        </Link>
        {datasetId ? (
          <Link
            href={`/data-lab/${datasetId}`}
            className="border border-[var(--line)] px-4 py-2 text-xs uppercase tracking-[0.14em] text-[var(--paper-dim)]"
          >
            Dataset detail
          </Link>
        ) : null}
      </div>

      {error ? <p className="mb-4 text-sm text-[var(--danger)]">{error}</p> : null}

      {stats ? (
        <div className="mb-8 grid gap-3 border border-[var(--line)] p-4 sm:grid-cols-2 lg:grid-cols-5">
          <p className="text-sm text-[var(--mist)]">
            Total <span className="text-[var(--paper)]">{stats.total}</span>
          </p>
          <p className="text-sm text-[var(--mist)]">
            Pending <span className="text-[var(--paper)]">{stats.by_status.pending ?? 0}</span>
          </p>
          <p className="text-sm text-[var(--mist)]">
            Approved <span className="text-[var(--paper)]">{stats.by_status.approved ?? 0}</span>
          </p>
          <p className="text-sm text-[var(--mist)]">
            ASR-sourced <span className="text-[var(--paper)]">{stats.asr_sourced}</span>
          </p>
          <p className="text-sm text-[var(--mist)]">
            Ingest <span className="text-[var(--paper)]">{stats.ingest_sourced}</span>
          </p>
        </div>
      ) : null}

      <div className="mb-6 grid gap-3 border border-[var(--line)] p-4 md:grid-cols-3">
        <select
          value={datasetId}
          onChange={(e) => setDatasetId(e.target.value)}
          className="border border-[var(--line)] bg-[var(--ink-soft)] px-3 py-2 text-[var(--paper)]"
        >
          <option value="">All datasets</option>
          {datasets.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name}
            </option>
          ))}
        </select>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="border border-[var(--line)] bg-[var(--ink-soft)] px-3 py-2 text-[var(--paper)]"
        >
          <option value="">All statuses</option>
          <option value="pending">pending</option>
          <option value="in_review">in_review</option>
          <option value="approved">approved</option>
          <option value="rejected">rejected</option>
          <option value="conflict">conflict</option>
        </select>
        <select
          value={filterMedia}
          onChange={(e) => setFilterMedia(e.target.value)}
          className="border border-[var(--line)] bg-[var(--ink-soft)] px-3 py-2 text-[var(--paper)]"
        >
          <option value="">All media</option>
          <option value="speech">speech</option>
          <option value="text">text</option>
          <option value="subtitle">subtitle</option>
          <option value="image">image</option>
        </select>
      </div>

      <form onSubmit={onCreate} className="mb-10 grid gap-3 border border-[var(--line)] p-5 md:grid-cols-3">
        <select
          value={datasetId}
          onChange={(e) => setDatasetId(e.target.value)}
          className="border border-[var(--line)] bg-[var(--ink-soft)] px-3 py-2 text-[var(--paper)]"
          required
        >
          {datasets.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name}
            </option>
          ))}
        </select>
        <select
          value={mediaType}
          onChange={(e) => setMediaType(e.target.value)}
          className="border border-[var(--line)] bg-[var(--ink-soft)] px-3 py-2 text-[var(--paper)]"
        >
          <option value="speech">speech</option>
          <option value="text">text</option>
          <option value="subtitle">subtitle</option>
        </select>
        <select
          value={dialect}
          onChange={(e) => setDialect(e.target.value)}
          className="border border-[var(--line)] bg-[var(--ink-soft)] px-3 py-2 text-[var(--paper)]"
        >
          <option value="sorani">Sorani</option>
          <option value="badini">Badini</option>
          <option value="kurmanji">Kurmanji</option>
        </select>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Transcript / source text"
          rows={3}
          className="md:col-span-3 border border-[var(--line)] bg-[var(--ink-soft)] px-3 py-2 text-[var(--paper)]"
          required
        />
        <input
          value={translation}
          onChange={(e) => setTranslation(e.target.value)}
          placeholder="Translation (optional)"
          className="md:col-span-3 border border-[var(--line)] bg-[var(--ink-soft)] px-3 py-2 text-[var(--paper)]"
        />
        <button
          type="submit"
          disabled={busy || !datasetId}
          className="md:col-span-3 border border-[var(--gold)] px-4 py-2 text-xs uppercase tracking-[0.14em] text-[var(--gold-bright)] disabled:opacity-50"
        >
          {busy ? "Saving…" : "Create annotation task"}
        </button>
      </form>

      <ul className="space-y-4">
        {tasks.map((t) => {
          const labels = (t.labels || {}) as {
            dialect?: string;
            translation?: string;
            source?: string;
            source_job_id?: string;
            needs_transcript?: boolean;
            average_confidence?: number;
          };
          const edit = edits[t.id] || {
            text: "",
            dialect: "sorani",
            translation: "",
            speaker: "speaker_1",
            consent: false,
            comment: "",
          };
          const asrSourced = Boolean(
            labels.source_job_id || labels.source === "asr" || labels.source === "ingest"
          );
          const open = expanded === t.id;
          const comments = (t.comments || []) as { by?: string; text?: string; at?: string }[];
          const history = (t.revision_history || []) as {
            by?: string;
            at?: string;
            before_status?: string;
          }[];

          return (
            <li key={t.id} className="border border-[var(--line)] px-4 py-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <p className="text-[var(--paper)]">
                    {t.media_type} · {t.status}
                    {asrSourced ? (
                      <span className="ml-2 text-[0.65rem] uppercase tracking-[0.12em] text-[var(--teal)]">
                        {labels.source_job_id ? "ASR" : labels.source || "ingest"}
                      </span>
                    ) : null}
                  </p>
                  <p className="mt-1 text-xs text-[var(--mist-soft)]">
                    {datasetName(t.dataset_id)}
                    {labels.source_job_id ? ` · job ${labels.source_job_id.slice(0, 8)}` : ""}
                    {labels.average_confidence != null
                      ? ` · conf ${labels.average_confidence}`
                      : ""}
                  </p>
                  <textarea
                    value={edit.text}
                    onChange={(e) => patchEdit(t.id, { text: e.target.value })}
                    rows={3}
                    className="mt-3 w-full border border-[var(--line)] bg-[var(--ink-soft)] px-3 py-2 text-sm text-[var(--paper)]"
                    placeholder={labels.needs_transcript ? "Transcript pending" : "Transcript"}
                  />
                  <div className="mt-3 grid gap-2 md:grid-cols-2 lg:grid-cols-4">
                    <select
                      value={edit.dialect}
                      onChange={(e) => patchEdit(t.id, { dialect: e.target.value })}
                      className="border border-[var(--line)] bg-[var(--ink-soft)] px-2 py-1.5 text-sm text-[var(--paper)]"
                    >
                      <option value="sorani">Sorani</option>
                      <option value="badini">Badini</option>
                      <option value="kurmanji">Kurmanji</option>
                    </select>
                    <input
                      value={edit.translation}
                      onChange={(e) => patchEdit(t.id, { translation: e.target.value })}
                      placeholder="Translation"
                      className="border border-[var(--line)] bg-[var(--ink-soft)] px-2 py-1.5 text-sm text-[var(--paper)]"
                    />
                    <input
                      value={edit.speaker}
                      onChange={(e) => patchEdit(t.id, { speaker: e.target.value })}
                      placeholder="Speaker"
                      className="border border-[var(--line)] bg-[var(--ink-soft)] px-2 py-1.5 text-sm text-[var(--paper)]"
                    />
                    <label className="flex items-center gap-2 text-sm text-[var(--mist)]">
                      <input
                        type="checkbox"
                        checked={edit.consent}
                        onChange={(e) => patchEdit(t.id, { consent: e.target.checked })}
                      />
                      Consent
                    </label>
                  </div>
                  <input
                    value={edit.comment}
                    onChange={(e) => patchEdit(t.id, { comment: e.target.value })}
                    placeholder="Review comment (required to reject)"
                    className="mt-2 w-full border border-[var(--line)] bg-[var(--ink-soft)] px-2 py-1.5 text-sm text-[var(--paper)]"
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => void saveReview(t, "in_review")}
                    className="border border-[var(--line)] px-3 py-1 text-[0.65rem] uppercase tracking-[0.14em] text-[var(--paper-dim)]"
                  >
                    In review
                  </button>
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => void saveReview(t, "approved")}
                    className="border border-[var(--teal)] px-3 py-1 text-[0.65rem] uppercase tracking-[0.14em] text-[var(--teal)]"
                  >
                    Approve
                  </button>
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => void saveReview(t, "rejected")}
                    className="border border-[var(--danger)] px-3 py-1 text-[0.65rem] uppercase tracking-[0.14em] text-[var(--danger)]"
                  >
                    Reject
                  </button>
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => void saveReview(t, "conflict")}
                    className="border border-[var(--gold)] px-3 py-1 text-[0.65rem] uppercase tracking-[0.14em] text-[var(--gold-bright)]"
                  >
                    Conflict
                  </button>
                  <button
                    type="button"
                    onClick={() => setExpanded(open ? null : t.id)}
                    className="border border-[var(--line)] px-3 py-1 text-[0.65rem] uppercase tracking-[0.14em] text-[var(--mist)]"
                  >
                    {open ? "Hide thread" : "Thread"}
                  </button>
                </div>
              </div>
              {open ? (
                <div className="mt-4 grid gap-4 border-t border-[var(--line)] pt-3 md:grid-cols-2">
                  <div>
                    <p className="text-[0.65rem] uppercase tracking-[0.12em] text-[var(--mist)]">
                      Comments
                    </p>
                    <ul className="mt-2 space-y-2 text-xs text-[var(--mist)]">
                      {comments.length ? (
                        comments.map((c, i) => (
                          <li key={`${t.id}-c-${i}`}>
                            <span className="text-[var(--paper-dim)]">{c.by}</span>: {c.text}
                          </li>
                        ))
                      ) : (
                        <li>No comments yet.</li>
                      )}
                    </ul>
                  </div>
                  <div>
                    <p className="text-[0.65rem] uppercase tracking-[0.12em] text-[var(--mist)]">
                      Revisions
                    </p>
                    <ul className="mt-2 space-y-2 text-xs text-[var(--mist)]">
                      {history.length ? (
                        history
                          .slice()
                          .reverse()
                          .slice(0, 8)
                          .map((h, i) => (
                            <li key={`${t.id}-h-${i}`}>
                              {h.at?.slice(0, 19)} · {h.by} · was {h.before_status}
                            </li>
                          ))
                      ) : (
                        <li>No revisions yet.</li>
                      )}
                    </ul>
                  </div>
                </div>
              ) : null}
            </li>
          );
        })}
        {!tasks.length ? (
          <li className="text-sm text-[var(--mist)]">No annotation tasks match filters.</li>
        ) : null}
      </ul>
    </>
  );
}

export default function AnnotationsPage() {
  return (
    <CoreShell
      title="Annotations"
      subtitle="Production review workspace — dialect, transcript, consent, approve / reject / conflict, export-ready labels."
    >
      <Suspense fallback={<p className="text-[var(--mist)]">Loading annotations…</p>}>
        <AnnotationsWorkspace />
      </Suspense>
    </CoreShell>
  );
}
