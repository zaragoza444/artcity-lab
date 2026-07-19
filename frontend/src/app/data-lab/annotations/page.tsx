"use client";

import { FormEvent, useEffect, useState } from "react";
import { CoreShell } from "@/components/CoreShell";
import { api, type AnnotationTask, type Dataset } from "@/lib/api";

export default function AnnotationsPage() {
  const [tasks, setTasks] = useState<AnnotationTask[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [datasetId, setDatasetId] = useState("");
  const [text, setText] = useState("");
  const [dialect, setDialect] = useState("sorani");
  const [translation, setTranslation] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function load() {
    Promise.all([api.listAnnotations(), api.listDatasets()])
      .then(([a, d]) => {
        setTasks(a);
        setDatasets(d);
        if (!datasetId && d[0]) setDatasetId(d[0].id);
      })
      .catch(() => undefined);
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
        labels: { dialect, translation: translation.trim() || null },
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

  async function onApprove(id: string) {
    setBusy(true);
    try {
      await api.updateAnnotation(id, { status: "approved", comment: "Approved in Data Lab" });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Update failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <CoreShell
      title="Annotations"
      subtitle="Dialect, translation, and speech transcript labels for Kurdish training manifests."
    >
      {error ? <p className="mb-4 text-sm text-[var(--danger)]">{error}</p> : null}

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
        {tasks.map((t) => (
          <li key={t.id} className="border border-[var(--line)] px-4 py-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-[var(--paper)]">
                  {t.media_type} · {t.status}
                </p>
                <p className="mt-1 text-sm text-[var(--mist)]">
                  {String((t.payload as { text?: string }).text || JSON.stringify(t.payload))}
                </p>
                <p className="mt-1 text-xs text-[var(--mist-soft)]">
                  dialect {(t.labels as { dialect?: string } | null)?.dialect || "—"} · translation{" "}
                  {(t.labels as { translation?: string } | null)?.translation || "—"}
                </p>
              </div>
              {t.status !== "approved" ? (
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => void onApprove(t.id)}
                  className="border border-[var(--teal)] px-3 py-1 text-[0.65rem] uppercase tracking-[0.14em] text-[var(--teal)]"
                >
                  Approve
                </button>
              ) : null}
            </div>
          </li>
        ))}
        {!tasks.length ? (
          <li className="text-sm text-[var(--mist)]">No annotation tasks yet.</li>
        ) : null}
      </ul>
    </CoreShell>
  );
}
