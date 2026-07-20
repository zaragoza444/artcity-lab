"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { CoreShell } from "@/components/CoreShell";
import { api, type Dataset, type IngestionRun } from "@/lib/api";

export default function DataLabPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [ingestions, setIngestions] = useState<IngestionRun[]>([]);
  const [datasetName, setDatasetName] = useState("");
  const [dialect, setDialect] = useState("sorani");
  const [lastReport, setLastReport] = useState<IngestionRun | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function load() {
    Promise.all([api.listDatasets(), api.listIngestions()])
      .then(([d, i]) => {
        setDatasets(d);
        setIngestions(i.slice(0, 8));
      })
      .catch((e) => setError(String(e.message || e)));
  }

  useEffect(() => {
    load();
  }, []);

  async function onIngest(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const input = form.elements.namedItem("files") as HTMLInputElement;
    if (!input.files?.length) {
      setError("Select at least one file");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const run = await api.ingestFiles({
        files: input.files,
        datasetName: datasetName.trim() || undefined,
        language: "ku",
        dialect,
      });
      setLastReport(run);
      input.value = "";
      setDatasetName("");
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ingest failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <CoreShell
      title="Data Lab"
      subtitle="Ingest archives, review rights, annotate labels, and export training manifests. Upload is not training."
    >
      <div className="mb-6 flex flex-wrap gap-4">
        <Link
          href="/data-lab/annotations"
          className="border border-[var(--line)] px-4 py-2 text-xs uppercase tracking-[0.14em] text-[var(--paper-dim)]"
        >
          Annotations
        </Link>
        <Link
          href="/rights"
          className="border border-[var(--line)] px-4 py-2 text-xs uppercase tracking-[0.14em] text-[var(--paper-dim)]"
        >
          Rights
        </Link>
      </div>

      {error ? <p className="mb-4 text-sm text-[var(--danger)]">{error}</p> : null}

      <form onSubmit={onIngest} className="mb-10 space-y-3 border border-[var(--line)] p-5">
        <p className="text-[0.7rem] uppercase tracking-[0.14em] text-[var(--mist)]">
          Ingest files
        </p>
        <input
          value={datasetName}
          onChange={(e) => setDatasetName(e.target.value)}
          placeholder="New dataset name (optional)"
          className="w-full border border-[var(--line)] bg-[var(--ink-soft)] px-3 py-2 text-[var(--paper)]"
        />
        <select
          value={dialect}
          onChange={(e) => setDialect(e.target.value)}
          className="w-full border border-[var(--line)] bg-[var(--ink-soft)] px-3 py-2 text-[var(--paper)]"
        >
          <option value="sorani">Sorani</option>
          <option value="badini">Badini</option>
          <option value="kurmanji">Kurmanji</option>
        </select>
        <input
          name="files"
          type="file"
          multiple
          className="w-full text-sm text-[var(--paper)] file:mr-3 file:border file:border-[var(--line)] file:bg-[var(--ink-soft)] file:px-3 file:py-1.5 file:text-xs file:uppercase file:tracking-[0.12em] file:text-[var(--gold-bright)]"
        />
        <button
          type="submit"
          disabled={busy}
          className="border border-[var(--gold)] bg-[rgba(197,161,94,0.14)] px-4 py-2 text-xs uppercase tracking-[0.14em] text-[var(--gold-bright)] disabled:opacity-50"
        >
          {busy ? "Ingesting…" : "Upload & ingest"}
        </button>
      </form>

      {lastReport?.report ? (
        <div className="mb-10 border border-[var(--teal)]/40 p-4 text-sm text-[var(--paper-dim)]">
          <p className="text-[0.7rem] uppercase tracking-[0.14em] text-[var(--teal)]">
            Last ingestion · {lastReport.status}
          </p>
          <p className="mt-2">
            imported {lastReport.report.imported ?? 0} · duplicates {lastReport.report.duplicates ?? 0}{" "}
            · failed {lastReport.report.failed ?? 0} · unknown rights{" "}
            {lastReport.report.unknown_rights ?? 0} ·{" "}
            {lastReport.report.total_bytes ?? 0} bytes
          </p>
          {lastReport.dataset_id ? (
            <Link
              href={`/data-lab/${lastReport.dataset_id}`}
              className="mt-2 inline-block text-xs uppercase tracking-[0.12em] text-[var(--gold-bright)]"
            >
              Open dataset
            </Link>
          ) : null}
        </div>
      ) : null}

      <div className="grid gap-10 lg:grid-cols-2">
        <section>
          <p className="mb-3 text-[0.7rem] uppercase tracking-[0.14em] text-[var(--mist)]">
            Datasets
          </p>
          <ul className="space-y-3">
            {datasets.map((d) => (
              <li key={d.id}>
                <Link
                  href={`/data-lab/${d.id}`}
                  className="block border border-[var(--line)] px-4 py-4 hover:border-[var(--gold)]"
                >
                  <div className="flex flex-wrap items-baseline justify-between gap-2">
                    <p className="text-[var(--paper)]">{d.name}</p>
                    <span className="text-[0.7rem] uppercase tracking-[0.14em] text-[var(--teal)]">
                      {d.status}
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-[var(--mist)]">
                    {d.category} · {d.media_type} · v{d.version} · {d.record_count} records
                    {d.ai_training_permission ? " · AI training permitted" : ""}
                  </p>
                </Link>
              </li>
            ))}
            {!datasets.length && !error ? (
              <p className="text-[var(--mist)]">No datasets yet. Ingest files above.</p>
            ) : null}
          </ul>
        </section>

        <section>
          <p className="mb-3 text-[0.7rem] uppercase tracking-[0.14em] text-[var(--mist)]">
            Recent ingestions
          </p>
          <ul className="space-y-3">
            {ingestions.map((run) => (
              <li key={run.id} className="border border-[var(--line)] px-4 py-3 text-sm text-[var(--mist)]">
                <div className="flex flex-wrap justify-between gap-2">
                  <span className="font-mono text-xs text-[var(--paper-dim)]">{run.id.slice(0, 8)}</span>
                  <span className="text-[0.65rem] uppercase tracking-[0.12em] text-[var(--teal)]">
                    {run.status}
                  </span>
                </div>
                <p className="mt-1">
                  +{run.report?.imported ?? 0} files · dup {run.report?.duplicates ?? 0} · fail{" "}
                  {run.report?.failed ?? 0}
                </p>
                {run.dataset_id ? (
                  <Link
                    href={`/data-lab/${run.dataset_id}`}
                    className="mt-1 inline-block text-xs text-[var(--gold-bright)]"
                  >
                    Dataset
                  </Link>
                ) : null}
              </li>
            ))}
            {!ingestions.length ? (
              <li className="text-sm text-[var(--mist)]">No ingestion runs yet.</li>
            ) : null}
          </ul>
        </section>
      </div>
    </CoreShell>
  );
}
