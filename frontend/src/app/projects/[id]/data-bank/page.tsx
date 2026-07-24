"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import {
  api,
  mediaAbsolute,
  withAccessToken,
  type DataBankAsset,
  type DataBankSummary,
  type Project,
} from "@/lib/api";
import { PageHeader } from "@/components/PageHeader";
import { SiteHeader } from "@/components/SiteHeader";

export default function ProjectDataBankPage() {
  const params = useParams();
  const projectId = String(params.id);

  const [project, setProject] = useState<Project | null>(null);
  const [summary, setSummary] = useState<DataBankSummary | null>(null);
  const [assets, setAssets] = useState<DataBankAsset[]>([]);
  const [q, setQ] = useState("");
  const [assetType, setAssetType] = useState("");
  const [selected, setSelected] = useState<DataBankAsset | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [p, s, rows] = await Promise.all([
        api.getProject(projectId),
        api.dataBankSummary(projectId),
        api.listDataBank(projectId, {
          q: q || undefined,
          asset_type: assetType || undefined,
        }),
      ]);
      setProject(p);
      setSummary(s);
      setAssets(rows);
      if (rows[0] && !selected) setSelected(rows[0]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load data bank");
    } finally {
      setLoading(false);
    }
  }, [projectId, q, assetType, selected]);

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  async function onSearch(e: FormEvent) {
    e.preventDefault();
    await load();
  }

  async function onUpload(e: FormEvent) {
    e.preventDefault();
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      const asset = await api.uploadDataBank(projectId, file, {
        tags: "data-bank,upload",
      });
      setFile(null);
      setSelected(asset);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  async function onSync() {
    setBusy(true);
    setError(null);
    try {
      await api.syncDataBank(projectId);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sync failed");
    } finally {
      setBusy(false);
    }
  }

  const preview = selected?.media_url
    ? withAccessToken(mediaAbsolute(selected.media_url) || "")
    : null;

  return (
    <main className="min-h-screen pb-20">
      <SiteHeader />
      <div className="ac-container pt-10 md:pt-14">
        <PageHeader
          eyebrow="Project Data Bank"
          title={project?.name || "Data Bank"}
          description="Upload reference files, sync Studio generations, and browse every project asset in one vault."
          actions={
            <div className="flex flex-wrap gap-3">
              <Link href="/data-bank" className="ac-btn">
                All banks
              </Link>
              <Link href={`/studio/${projectId}`} className="ac-btn">
                Studio
              </Link>
              <button type="button" className="ac-btn ac-btn-primary" disabled={busy} onClick={() => void onSync()}>
                {busy ? "Working…" : "Sync generations"}
              </button>
            </div>
          }
        />

        {error ? <p className="mb-6 text-[var(--danger)]">{error}</p> : null}

        <div className="mb-8 grid gap-4 sm:grid-cols-3">
          <Stat label="Assets" value={String(summary?.total ?? 0)} />
          <Stat
            label="Types"
            value={Object.entries(summary?.by_type || {})
              .map(([k, v]) => `${k}:${v}`)
              .join(" · ") || "—"}
          />
          <Stat
            label="Sources"
            value={Object.entries(summary?.by_source || {})
              .map(([k, v]) => `${k}:${v}`)
              .join(" · ") || "—"}
          />
        </div>

        <div className="grid gap-10 lg:grid-cols-[1fr_1.1fr]">
          <div className="space-y-8">
            <form onSubmit={onSearch} className="flex flex-wrap gap-3">
              <input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Search name, prompt, tags"
                className="min-w-[12rem] flex-1 border border-[var(--line)] bg-[rgba(10,15,22,0.55)] px-3 py-2 text-sm outline-none focus:border-[var(--gold)]"
              />
              <select
                value={assetType}
                onChange={(e) => setAssetType(e.target.value)}
                className="border border-[var(--line)] bg-[rgba(10,15,22,0.55)] px-3 py-2 text-sm"
              >
                <option value="">All types</option>
                {["image", "video", "voice", "audio", "music", "script", "other"].map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
              <button type="submit" className="ac-btn">
                Search
              </button>
            </form>

            <form onSubmit={onUpload} className="space-y-3 border border-[var(--line)] p-4">
              <p className="ac-display text-[0.68rem] tracking-[0.18em] text-[var(--mist)] uppercase">
                Upload to bank
              </p>
              <input
                type="file"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="block w-full text-sm text-[var(--mist)]"
              />
              <button type="submit" disabled={!file || busy} className="ac-btn ac-btn-primary">
                {busy ? "Uploading…" : "Upload file"}
              </button>
            </form>

            {loading ? (
              <p className="text-[0.8rem] tracking-[0.18em] text-[var(--mist)] uppercase">Loading…</p>
            ) : assets.length === 0 ? (
              <p className="text-sm text-[var(--mist)]">Bank empty — upload a file or sync Studio generations.</p>
            ) : (
              <ul className="border-t border-[var(--line)]">
                {assets.map((a) => (
                  <li key={a.id}>
                    <button
                      type="button"
                      onClick={() => setSelected(a)}
                      className={`ac-row w-full text-left ${
                        selected?.id === a.id ? "text-[var(--gold-bright)]" : ""
                      }`}
                    >
                      <div className="py-4">
                        <p className="ac-display text-lg tracking-tight">{a.name}</p>
                        <p className="mt-1 text-[0.68rem] uppercase tracking-[0.14em] text-[var(--mist-soft)]">
                          {a.asset_type} · {a.source || "—"} ·{" "}
                          {a.created_at ? new Date(a.created_at).toLocaleString() : ""}
                        </p>
                      </div>
                      <div className="ac-rule" />
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="border border-[var(--line)] bg-[rgba(10,15,22,0.35)] p-5">
            {selected && preview ? (
              <div className="space-y-4">
                <p className="ac-display text-[0.68rem] tracking-[0.18em] text-[var(--mist)] uppercase">
                  Preview · {selected.asset_type}
                </p>
                {selected.asset_type === "image" || selected.content_type?.startsWith("image/") ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={preview}
                    alt={selected.name}
                    className="w-full border border-[var(--line)] bg-black object-cover aspect-video"
                  />
                ) : selected.asset_type === "video" || selected.content_type?.startsWith("video/") ? (
                  <video controls src={preview} className="w-full border border-[var(--line)] bg-black aspect-video" />
                ) : selected.asset_type === "audio" ||
                  selected.asset_type === "voice" ||
                  selected.asset_type === "music" ? (
                  <audio controls src={preview} className="w-full" />
                ) : (
                  <a href={preview} className="text-[var(--gold)]" target="_blank" rel="noreferrer">
                    Open file
                  </a>
                )}
                <p className="text-sm text-[var(--mist-soft)]">{selected.prompt || selected.name}</p>
                {selected.tags?.length ? (
                  <p className="text-[0.68rem] uppercase tracking-[0.14em] text-[var(--mist)]">
                    {selected.tags.join(" · ")}
                  </p>
                ) : null}
              </div>
            ) : (
              <p className="text-sm text-[var(--mist)]">Select an asset to preview.</p>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-[var(--line)] bg-[rgba(10,15,22,0.35)] px-4 py-4">
      <p className="ac-display text-[0.65rem] tracking-[0.18em] text-[var(--mist)] uppercase">{label}</p>
      <p className="mt-2 text-sm text-[var(--paper)] break-words">{value}</p>
    </div>
  );
}
