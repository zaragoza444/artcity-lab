"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { CoreShell } from "@/components/CoreShell";
import { graphicMotionApi, type AgmJob, type AgmScene } from "@/lib/api";

export default function GraphicMotionScenePage() {
  const params = useParams();
  const sceneId = String(params.sceneId || "");
  const [scene, setScene] = useState<AgmScene | null>(null);
  const [job, setJob] = useState<AgmJob | null>(null);
  const [validation, setValidation] = useState<string>("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(() => {
    if (!sceneId) return;
    graphicMotionApi
      .getScene(sceneId)
      .then(setScene)
      .catch((e) => setError(String(e.message || e)));
  }, [sceneId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    if (!job || ["completed", "failed", "cancelled"].includes(job.status)) return;
    const t = setInterval(() => {
      graphicMotionApi
        .getJob(job.id)
        .then(setJob)
        .catch(() => undefined);
    }, 800);
    return () => clearInterval(t);
  }, [job]);

  async function runValidate() {
    setBusy(true);
    setError("");
    try {
      const r = await graphicMotionApi.validateScene(sceneId);
      setValidation(r.valid ? "Valid" : r.error_codes.join(", "));
    } catch (e) {
      setError(String((e as Error).message || e));
    } finally {
      setBusy(false);
    }
  }

  async function runPreview() {
    setBusy(true);
    setError("");
    try {
      const j = await graphicMotionApi.preview(sceneId, { mode: "still", format: "png", at_ms: 900 });
      setJob(j);
    } catch (e) {
      setError(String((e as Error).message || e));
    } finally {
      setBusy(false);
    }
  }

  async function runRender() {
    setBusy(true);
    setError("");
    try {
      const j = await graphicMotionApi.render(sceneId, {
        profile: {
          container: "mp4",
          codec: "h264",
          width: 1920,
          height: 1080,
          fps: 25,
          color_space: "rec709",
        },
      });
      setJob(j);
    } catch (e) {
      setError(String((e as Error).message || e));
    } finally {
      setBusy(false);
    }
  }

  const graphText = scene?.revision?.graph
    ? JSON.stringify(scene.revision.graph, null, 2)
    : "";

  return (
    <CoreShell
      title={scene?.name || "Scene"}
      subtitle={scene ? `${scene.locale} · ${scene.direction} · etag ${scene.etag?.slice(0, 12) || "—"}` : sceneId}
    >
      <Link href="/graphic-motion" className="text-[0.75rem] text-[var(--mist)] hover:text-[var(--paper)]">
        ← Graphic Motion
      </Link>
      {error ? <p className="mt-3 text-[var(--danger)]">{error}</p> : null}
      <div className="mt-6 flex flex-wrap gap-2">
        <button
          type="button"
          disabled={busy}
          onClick={runValidate}
          className="border border-[var(--line)] px-3 py-1.5 text-[0.7rem] uppercase tracking-[0.12em] text-[var(--paper)]"
        >
          Validate
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={runPreview}
          className="border border-[var(--gold)] px-3 py-1.5 text-[0.7rem] uppercase tracking-[0.12em] text-[var(--gold-bright)]"
        >
          Queue preview
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={runRender}
          className="border border-[var(--line)] px-3 py-1.5 text-[0.7rem] uppercase tracking-[0.12em] text-[var(--mist)]"
        >
          Queue render
        </button>
      </div>
      {validation ? (
        <p className="mt-4 text-[0.85rem] text-[var(--paper-dim)]">Validation: {validation}</p>
      ) : null}
      {job ? (
        <div className="mt-6 border border-[var(--line)] px-4 py-4">
          <p className="text-[0.7rem] uppercase tracking-[0.14em] text-[var(--gold-bright)]">Job</p>
          <p className="mt-2 text-[var(--paper)]">
            {job.job_kind} · {job.status} · {Math.round((job.progress || 0) * 100)}%
          </p>
          {job.acx_quote_id ? (
            <p className="mt-1 text-[0.75rem] text-[var(--mist)]">ACX quote {job.acx_quote_id}</p>
          ) : null}
          {job.error_message ? <p className="mt-1 text-[var(--danger)]">{job.error_message}</p> : null}
          {job.outputs?.[0]?.asset_id ? (
            <p className="mt-1 text-[0.8rem] text-[var(--paper-dim)]">
              Asset {job.outputs[0].asset_id}
              {job.outputs[0].checksum ? ` · ${job.outputs[0].checksum.slice(0, 12)}…` : ""}
            </p>
          ) : null}
        </div>
      ) : null}
      {graphText ? (
        <pre
          className="mt-8 max-h-[28rem] overflow-auto border border-[var(--line)] p-4 text-[0.7rem] text-[var(--mist)]"
          dir="auto"
        >
          {graphText}
        </pre>
      ) : null}
    </CoreShell>
  );
}
