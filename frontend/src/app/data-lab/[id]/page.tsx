"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { CoreShell } from "@/components/CoreShell";
import { api, type DatasetDetail, type DatasetFile } from "@/lib/api";
import { getAccessToken } from "@/lib/auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const STATUS_OPTIONS = [
  "needs_review",
  "verified",
  "training_ready",
  "evaluation_only",
  "reference_only",
  "blocked",
  "archived",
];

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function DatasetDetailPage() {
  const params = useParams();
  const datasetId = String(params.id);
  const [detail, setDetail] = useState<DatasetDetail | null>(null);
  const [files, setFiles] = useState<DatasetFile[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewName, setPreviewName] = useState<string | null>(null);

  async function load() {
    try {
      const [d, f] = await Promise.all([
        api.getDatasetDetail(datasetId),
        api.listDatasetFiles(datasetId),
      ]);
      setDetail(d);
      setFiles(f);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed");
    }
  }

  useEffect(() => {
    void load();
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [datasetId]);

  async function setStatus(status: string) {
    setBusy(true);
    setError(null);
    try {
      await api.updateDatasetStatus(datasetId, status);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Status update failed");
    } finally {
      setBusy(false);
    }
  }

  async function onExport(format: "jsonl" | "csv") {
    setBusy(true);
    setError(null);
    try {
      const blob = await api.exportDataset(datasetId, format, true);
      triggerDownload(blob, `${detail?.name || "dataset"}-export.${format}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed");
    } finally {
      setBusy(false);
    }
  }

  async function onManifest() {
    setBusy(true);
    setError(null);
    try {
      const manifest = await api.getDatasetManifest(datasetId);
      const blob = new Blob([JSON.stringify(manifest, null, 2)], { type: "application/json" });
      triggerDownload(blob, `${detail?.name || "dataset"}-manifest.json`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Manifest failed");
    } finally {
      setBusy(false);
    }
  }

  async function previewFile(file: DatasetFile) {
    setBusy(true);
    setError(null);
    try {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      const token = getAccessToken();
      const headers: Record<string, string> = {};
      if (token) headers.Authorization = `Bearer ${token}`;
      const res = await fetch(`${API_URL}${file.media_url}`, { headers, cache: "no-store" });
      if (!res.ok) throw new Error(`Preview failed (${res.status})`);
      const blob = await res.blob();
      setPreviewUrl(URL.createObjectURL(blob));
      setPreviewName(file.filename);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Preview failed");
    } finally {
      setBusy(false);
    }
  }

  if (!detail && !error) {
    return (
      <CoreShell title="Dataset" subtitle="Loading…">
        <p className="text-[var(--mist)]">Loading dataset…</p>
      </CoreShell>
    );
  }

  if (!detail) {
    return (
      <CoreShell title="Dataset" subtitle="Not found">
        <p className="text-[var(--danger)]">{error}</p>
        <Link href="/data-lab" className="mt-4 inline-block text-[var(--gold-bright)]">
          Back to Data Lab
        </Link>
      </CoreShell>
    );
  }

  return (
    <CoreShell title={detail.name} subtitle={`${detail.status} · ${detail.media_type} · v${detail.version}`}>
      <div className="mb-6 flex flex-wrap gap-3">
        <Link
          href="/data-lab"
          className="border border-[var(--line)] px-3 py-1.5 text-xs uppercase tracking-[0.12em] text-[var(--paper-dim)]"
        >
          All datasets
        </Link>
        <Link
          href={`/data-lab/annotations?dataset=${detail.id}`}
          className="border border-[var(--line)] px-3 py-1.5 text-xs uppercase tracking-[0.12em] text-[var(--paper-dim)]"
        >
          Annotations
        </Link>
        <Link
          href="/rights"
          className="border border-[var(--line)] px-3 py-1.5 text-xs uppercase tracking-[0.12em] text-[var(--paper-dim)]"
        >
          Rights
        </Link>
      </div>

      {error ? <p className="mb-4 text-sm text-[var(--danger)]">{error}</p> : null}

      <div className="mb-8 grid gap-4 border border-[var(--line)] p-5 md:grid-cols-3">
        <p className="text-sm text-[var(--mist)]">
          Files <span className="text-[var(--paper)]">{detail.file_count}</span>
        </p>
        <p className="text-sm text-[var(--mist)]">
          Approved labels <span className="text-[var(--paper)]">{detail.approved_annotations}</span>
        </p>
        <p className="text-sm text-[var(--mist)]">
          Pending <span className="text-[var(--paper)]">{detail.pending_annotations}</span>
        </p>
        <p className="text-sm text-[var(--mist)] md:col-span-3">
          Language {detail.language || "—"} · dialect {detail.dialect || "—"} ·{" "}
          {detail.record_count} records · {detail.size_bytes ?? 0} bytes
        </p>
        <p className="text-sm text-[var(--mist)] md:col-span-3">
          Rights:{" "}
          {detail.rights
            ? `${detail.rights.legal_status} · ${detail.rights.copyright_owner}${
                detail.rights.ai_training ? " · AI training" : ""
              }`
            : "none on file — attach via Rights before training_ready"}
        </p>
      </div>

      <div className="mb-8 flex flex-wrap items-end gap-3 border border-[var(--line)] p-5">
        <label className="text-sm text-[var(--mist)]">
          Status
          <select
            value={detail.status}
            disabled={busy}
            onChange={(e) => void setStatus(e.target.value)}
            className="mt-1 block min-w-[12rem] border border-[var(--line)] bg-[var(--ink-soft)] px-3 py-2 text-[var(--paper)]"
          >
            {Array.from(new Set([detail.status, ...STATUS_OPTIONS])).map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
        <button
          type="button"
          disabled={busy}
          onClick={() => void onExport("jsonl")}
          className="border border-[var(--gold)] px-3 py-2 text-xs uppercase tracking-[0.12em] text-[var(--gold-bright)]"
        >
          Export JSONL
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={() => void onExport("csv")}
          className="border border-[var(--line)] px-3 py-2 text-xs uppercase tracking-[0.12em] text-[var(--paper-dim)]"
        >
          Export CSV
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={() => void onManifest()}
          className="border border-[var(--line)] px-3 py-2 text-xs uppercase tracking-[0.12em] text-[var(--paper-dim)]"
        >
          Manifest
        </button>
      </div>

      {previewUrl ? (
        <div className="mb-8 border border-[var(--line)] p-4">
          <p className="mb-2 text-xs uppercase tracking-[0.12em] text-[var(--mist)]">
            Preview · {previewName}
          </p>
          {previewName?.match(/\.(png|jpe?g|gif|webp)$/i) ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={previewUrl} alt={previewName || "preview"} className="max-h-80 border border-[var(--line)]" />
          ) : previewName?.match(/\.(wav|mp3|m4a|ogg)$/i) ? (
            <audio controls src={previewUrl} className="w-full" />
          ) : (
            <a href={previewUrl} download={previewName || "file"} className="text-[var(--gold-bright)]">
              Download preview
            </a>
          )}
        </div>
      ) : null}

      <p className="mb-3 text-[0.7rem] uppercase tracking-[0.14em] text-[var(--mist)]">
        File inventory
      </p>
      <ul className="space-y-2">
        {files.map((f) => (
          <li
            key={f.id}
            className="flex flex-wrap items-center justify-between gap-3 border border-[var(--line)] px-4 py-3 text-sm"
          >
            <div>
              <p className="text-[var(--paper)]">{f.filename}</p>
              <p className="text-xs text-[var(--mist)]">
                {f.media_type} · {f.size_bytes} bytes · {f.rights_status}
                {f.duration_seconds != null ? ` · ${f.duration_seconds.toFixed(1)}s` : ""}
              </p>
            </div>
            <button
              type="button"
              disabled={busy}
              onClick={() => void previewFile(f)}
              className="border border-[var(--line)] px-3 py-1 text-[0.65rem] uppercase tracking-[0.12em] text-[var(--gold-bright)]"
            >
              Preview
            </button>
          </li>
        ))}
        {!files.length ? (
          <li className="text-sm text-[var(--mist)]">No files ingested yet.</li>
        ) : null}
      </ul>
    </CoreShell>
  );
}
