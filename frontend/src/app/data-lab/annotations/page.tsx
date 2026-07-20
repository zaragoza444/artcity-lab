"use client";

import Link from "next/link";
import { FormEvent, Suspense, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { CoreShell } from "@/components/CoreShell";
import { api, type AnnotationTask, type Dataset } from "@/lib/api";

function AnnotationsWorkspace() {
  const search = useSearchParams();
  const initialDataset = search.get("dataset") || "";

  const [tasks, setTasks] = useState<AnnotationTask[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [datasetId, setDatasetId] = useState(initialDataset);
  const [filterStatus, setFilterStatus] = useState("");
  const [filterMedia, setFilterMedia] = useState("");
  const [text, setText] = useState("");
  const [dialect, setDialect] = useState("sorani");
  const [translation, setTranslation] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editLabels, setEditLabels] = useState<Record<string, { dialect: string; translation: string }>>(
    {}
  );

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
    ])
      .then(([a, d]) => {
        setTasks(a);
        setDatasets(d);
        if (!datasetId && d[0]) setDatasetId(d[0].id);
        const edits: Record<string, { dialect: string; translation: string }> = {};
        for (const t of a) {
          const labels = (t.labels || {}) as { dialect?: string; translation?: string };
          edits[t.id] = {
            dialect: labels.dialect || "sorani",
            translation: labels.translation || "",
          };
        }
        setEditLabels(edits);
      })
      .catch(() => undefined);
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
        media_type: "speech",
        payload: { text: text.trim(), language: "ku" },
        labels: { dialect, translation: translation.trim() || null, source: "manual" },
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

  async function saveLabels(task: AnnotationTask) {
    const edit = editLabels[task.id];
    if (!edit) return;
    setBusy(true);
    setError(null);
    try {
      await api.updateAnnotation(task.id, {
        labels: {
          ...(task.labels || {}),
          dialect: edit.dialect,
          translation: edit.translation.trim() || null,
        },
        status: "in_review",
        comment: "Labels updated in Data Lab",
      });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Update failed");
    } finally {
      setBusy(false);
    }
  }

  async function setStatus(id: string, status: string, comment: string) {
    setBusy(true);
    setError(null);
    try {
      await api.updateAnnotation(id, { status, comment });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Update failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <div className="mb-6">
        <Link
          href="/data-lab"
          className="border border-[var(--line)] px-4 py-2 text-xs uppercase tracking-[0.14em] text-[var(--paper-dim)]"
        >
          Data Lab
        </Link>
      </div>

      {error ? <p className="mb-4 text-sm text-[var(--danger)]">{error}</p> : null}

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

      <form onSubmit={onCreate} className="mb-10 grid gap-3 border border-[var(--line)] p-5 md:grid-cols-2">
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
          className="md:col-span-2 border border-[var(--line)] bg-[var(--ink-soft)] px-3 py-2 text-[var(--paper)]"
          required
        />
        <input
          value={translation}
          onChange={(e) => setTranslation(e.target.value)}
          placeholder="Translation (optional)"
          className="md:col-span-2 border border-[var(--line)] bg-[var(--ink-soft)] px-3 py-2 text-[var(--paper)]"
        />
        <button
          type="submit"
          disabled={busy || !datasetId}
          className="md:col-span-2 border border-[var(--gold)] px-4 py-2 text-xs uppercase tracking-[0.14em] text-[var(--gold-bright)] disabled:opacity-50"
        >
          {busy ? "Saving…" : "Create annotation task"}
        </button>
      </form>

      <ul className="space-y-3">
        {tasks.map((t) => {
          const labels = (t.labels || {}) as {
            dialect?: string;
            translation?: string;
            source?: string;
            source_job_id?: string;
            needs_transcript?: boolean;
          };
          const payload = t.payload as { text?: string; filename?: string };
          const edit = editLabels[t.id] || { dialect: "sorani", translation: "" };
          const asrSourced = Boolean(
            labels.source_job_id || labels.source === "asr" || labels.source === "ingest"
          );
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
                    {payload.filename ? ` · ${payload.filename}` : ""}
                    {labels.source_job_id ? ` · job ${labels.source_job_id.slice(0, 8)}` : ""}
                  </p>
                  <p className="mt-2 text-sm text-[var(--mist)]">
                    {payload.text ||
                      (labels.needs_transcript ? "(transcript pending)" : JSON.stringify(t.payload))}
                  </p>
                  <div className="mt-3 grid gap-2 md:grid-cols-2">
                    <select
                      value={edit.dialect}
                      onChange={(e) =>
                        setEditLabels((prev) => ({
                          ...prev,
                          [t.id]: { ...edit, dialect: e.target.value },
                        }))
                      }
                      className="border border-[var(--line)] bg-[var(--ink-soft)] px-2 py-1.5 text-sm text-[var(--paper)]"
                    >
                      <option value="sorani">Sorani</option>
                      <option value="badini">Badini</option>
                      <option value="kurmanji">Kurmanji</option>
                    </select>
                    <input
                      value={edit.translation}
                      onChange={(e) =>
                        setEditLabels((prev) => ({
                          ...prev,
                          [t.id]: { ...edit, translation: e.target.value },
                        }))
                      }
                      placeholder="Translation"
                      className="border border-[var(--line)] bg-[var(--ink-soft)] px-2 py-1.5 text-sm text-[var(--paper)]"
                    />
                  </div>
                </div>
                <div className="flex flex-col gap-2">
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => void saveLabels(t)}
                    className="border border-[var(--line)] px-3 py-1 text-[0.65rem] uppercase tracking-[0.14em] text-[var(--paper-dim)]"
                  >
                    Save · review
                  </button>
                  {t.status !== "approved" ? (
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() => void setStatus(t.id, "approved", "Approved in Data Lab")}
                      className="border border-[var(--teal)] px-3 py-1 text-[0.65rem] uppercase tracking-[0.14em] text-[var(--teal)]"
                    >
                      Approve
                    </button>
                  ) : null}
                  {t.status !== "rejected" ? (
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() => {
                        const reason = window.prompt("Reject reason") || "";
                        if (!reason.trim()) return;
                        void setStatus(t.id, "rejected", reason.trim());
                      }}
                      className="border border-[var(--danger)] px-3 py-1 text-[0.65rem] uppercase tracking-[0.14em] text-[var(--danger)]"
                    >
                      Reject
                    </button>
                  ) : null}
                </div>
              </div>
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
      subtitle="Dialect, translation, and speech transcript labels for Kurdish training manifests."
    >
      <Suspense fallback={<p className="text-[var(--mist)]">Loading annotations…</p>}>
        <AnnotationsWorkspace />
      </Suspense>
    </CoreShell>
  );
}
