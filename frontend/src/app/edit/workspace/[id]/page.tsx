"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api, type EditMediaAsset, type EditProject } from "@/lib/api";
import { PageHeader } from "@/components/PageHeader";
import { SiteHeader } from "@/components/SiteHeader";

export default function EditWorkspacePage() {
  const params = useParams();
  const workspaceId = String(params.id);
  const [assets, setAssets] = useState<EditMediaAsset[]>([]);
  const [projects, setProjects] = useState<EditProject[]>([]);
  const [title, setTitle] = useState("Interview cutdown");
  const [assetId, setAssetId] = useState("");
  const [rights, setRights] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const load = async () => {
    try {
      const [a, p] = await Promise.all([
        api.editListAssets(workspaceId),
        api.editListProjects(workspaceId),
      ]);
      setAssets(a);
      setProjects(p);
      if (!assetId && a[0]) setAssetId(a[0].id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load workspace");
    }
  };

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workspaceId]);

  const onUpload = async (file: File | null) => {
    if (!file) return;
    if (!rights) {
      setError("Confirm rights attestation before upload.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const asset = await api.editUploadAsset(workspaceId, file, true, "Uploader attested rights");
      setMessage(`Uploaded ${asset.filename}`);
      setAssetId(asset.id);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  };

  const createProject = async () => {
    if (!assetId) {
      setError("Upload or select a source asset first.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const project = await api.editCreateProject(workspaceId, {
        title,
        source_asset_id: assetId,
        brief: {
          objective: "engagement",
          platforms: ["instagram_reels", "youtube_shorts"],
          target_duration: { min: 25, max: 50 },
          languages: ["ckb", "en"],
        },
      });
      window.location.href = `/edit/${project.id}`;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Create failed");
      setBusy(false);
    }
  };

  return (
    <main className="min-h-screen pb-20">
      <SiteHeader />
      <div className="ac-container pt-10 md:pt-14">
        <PageHeader
          eyebrow="Art City Edit"
          title="Workspace ingest"
          description="Upload authorised long-form video with rights attestation, then create an Edit project."
          actions={
            <Link href="/edit" className="ac-btn">
              All projects
            </Link>
          }
        />

        {error ? <p className="mb-4 text-[var(--danger)]">{error}</p> : null}
        {message ? <p className="mb-4 text-[var(--mist)]">{message}</p> : null}

        <section className="mb-12 border border-[var(--line)] p-6">
          <h2 className="ac-display text-xl text-[var(--paper)]">Upload source</h2>
          <label className="mt-4 flex items-start gap-3 text-sm text-[var(--mist)]">
            <input
              type="checkbox"
              checked={rights}
              onChange={(e) => setRights(e.target.checked)}
              className="mt-1"
            />
            I own or am authorised to process this material (rights attestation required).
          </label>
          <input
            type="file"
            accept="video/*,audio/*"
            className="mt-4 block w-full text-sm text-[var(--mist)]"
            disabled={busy}
            onChange={(e) => void onUpload(e.target.files?.[0] ?? null)}
          />
        </section>

        <section className="mb-12 border border-[var(--line)] p-6">
          <h2 className="ac-display text-xl text-[var(--paper)]">New project</h2>
          <input
            className="ac-input mt-4 w-full max-w-lg"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Project title"
          />
          <select
            className="ac-input mt-3 w-full max-w-lg"
            value={assetId}
            onChange={(e) => setAssetId(e.target.value)}
          >
            <option value="">Select source asset</option>
            {assets.map((a) => (
              <option key={a.id} value={a.id}>
                {a.filename} · {(a.size_bytes / 1024 / 1024).toFixed(1)} MB
              </option>
            ))}
          </select>
          <button
            type="button"
            className="ac-btn ac-btn-primary mt-4"
            disabled={busy}
            onClick={() => void createProject()}
          >
            Create & open
          </button>
        </section>

        <section>
          <h2 className="ac-display mb-4 text-xl text-[var(--paper)]">Projects in workspace</h2>
          <ul className="border-t border-[var(--line)]">
            {projects.map((p) => (
              <li key={p.id} className="ac-row">
                <Link href={`/edit/${p.id}`} className="block py-5">
                  <span className="ac-display text-lg">{p.title}</span>
                  <span className="ml-4 text-[0.72rem] tracking-[0.14em] text-[var(--mist-soft)] uppercase">
                    {p.status}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </main>
  );
}
