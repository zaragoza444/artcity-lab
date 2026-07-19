"use client";

import { FormEvent, useEffect, useState } from "react";
import { CoreShell } from "@/components/CoreShell";
import { api, type AsrManifest, type SpeechDialect, type SpeechUploadResult } from "@/lib/api";

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function SpeechPage() {
  const [dialects, setDialects] = useState<SpeechDialect[]>([]);
  const [model, setModel] = useState("AC-KURDISH-ASR-v1");
  const [dialect, setDialect] = useState("sorani");
  const [audioKey, setAudioKey] = useState("");
  const [uploadInfo, setUploadInfo] = useState<SpeechUploadResult | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [detectText, setDetectText] = useState("Silav, Newroz û Zagros");
  const [detection, setDetection] = useState<string | null>(null);
  const [manifest, setManifest] = useState<AsrManifest | null>(null);
  const [recentJobs, setRecentJobs] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listSpeechDialects()
      .then((r) => {
        setDialects(r.dialects);
        setModel(r.model);
      })
      .catch(() => undefined);
    try {
      const raw = localStorage.getItem("artcity.speech.recentJobs");
      if (raw) setRecentJobs(JSON.parse(raw) as string[]);
    } catch {
      /* ignore */
    }
  }, []);

  function rememberJob(jobId: string) {
    setRecentJobs((prev) => {
      const next = [jobId, ...prev.filter((id) => id !== jobId)].slice(0, 8);
      localStorage.setItem("artcity.speech.recentJobs", JSON.stringify(next));
      return next;
    });
  }

  async function onDetect(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const r = await api.detectLanguage(detectText);
      setDetection(`${r.language}/${r.dialect} · ${r.script} · conf ${r.confidence}`);
      setDialect(r.dialect);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Detect failed");
    } finally {
      setBusy(false);
    }
  }

  async function onUpload(file: File | null) {
    if (!file) return;
    setBusy(true);
    setError(null);
    setFileName(file.name);
    try {
      const uploaded = await api.uploadSpeechAudio(file);
      setUploadInfo(uploaded);
      setAudioKey(uploaded.audio_storage_key);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  async function onAsr(e: FormEvent) {
    e.preventDefault();
    if (!audioKey.trim()) {
      setError("Upload audio or enter a storage key first");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const r = await api.runAsr({
        audio_storage_key: audioKey.trim(),
        dialect,
        project_id: uploadInfo?.project_id,
        create_annotation: true,
      });
      setManifest(r);
      if (r.job_id) rememberJob(r.job_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "ASR failed");
    } finally {
      setBusy(false);
    }
  }

  async function loadJob(jobId: string) {
    setBusy(true);
    setError(null);
    try {
      const r = await api.getSpeechJob(jobId);
      setManifest(r);
      if (r.audio_storage_key) setAudioKey(r.audio_storage_key);
      if (r.dialect) setDialect(r.dialect);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load job failed");
    } finally {
      setBusy(false);
    }
  }

  async function download(kind: "vtt" | "srt" | "json") {
    if (!manifest?.job_id) return;
    setBusy(true);
    setError(null);
    try {
      if (kind === "json") {
        const blob = await api.downloadSpeechTranscript(manifest.job_id);
        triggerDownload(blob, `transcript-${manifest.job_id}.json`);
      } else {
        const blob = await api.downloadSpeechSubtitle(manifest.job_id, kind);
        triggerDownload(blob, `subtitles-${manifest.job_id}.${kind}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Download failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <CoreShell
      title="Kurdish Speech"
      subtitle={`${model} — upload audio, transcribe Sorani / Badini / Kurmanji, download VTT/SRT.`}
    >
      {error ? <p className="mb-4 text-sm text-[var(--danger)]">{error}</p> : null}

      <div className="grid gap-8 lg:grid-cols-2">
        <form onSubmit={onDetect} className="space-y-3 border border-[var(--line)] p-5">
          <p className="text-[0.7rem] uppercase tracking-[0.14em] text-[var(--mist)]">
            Language / dialect detect
          </p>
          <textarea
            value={detectText}
            onChange={(e) => setDetectText(e.target.value)}
            rows={4}
            className="w-full border border-[var(--line)] bg-[var(--ink-soft)] px-3 py-2 text-[var(--paper)]"
          />
          <button
            type="submit"
            disabled={busy}
            className="border border-[var(--gold)] px-4 py-2 text-xs uppercase tracking-[0.14em] text-[var(--gold-bright)]"
          >
            Detect
          </button>
          {detection ? <p className="text-sm text-[var(--teal)]">{detection}</p> : null}
        </form>

        <form onSubmit={onAsr} className="space-y-3 border border-[var(--line)] p-5">
          <p className="text-[0.7rem] uppercase tracking-[0.14em] text-[var(--mist)]">
            Transcribe audio
          </p>
          <label className="block">
            <span className="mb-1 block text-xs text-[var(--mist)]">Audio file</span>
            <input
              type="file"
              accept="audio/*,.wav,.mp3,.m4a,.ogg"
              onChange={(e) => void onUpload(e.target.files?.[0] ?? null)}
              className="w-full text-sm text-[var(--paper)] file:mr-3 file:border file:border-[var(--line)] file:bg-[var(--ink-soft)] file:px-3 file:py-1.5 file:text-xs file:uppercase file:tracking-[0.12em] file:text-[var(--gold-bright)]"
            />
          </label>
          {uploadInfo ? (
            <p className="text-xs text-[var(--teal)]">
              Uploaded {fileName ?? "audio"} · {uploadInfo.bytes} bytes
              {uploadInfo.duration_seconds != null
                ? ` · ${uploadInfo.duration_seconds.toFixed(1)}s`
                : ""}
            </p>
          ) : null}
          <input
            value={audioKey}
            onChange={(e) => setAudioKey(e.target.value)}
            className="w-full border border-[var(--line)] bg-[var(--ink-soft)] px-3 py-2 text-[var(--paper)]"
            placeholder="or paste MinIO audio storage key"
          />
          <select
            value={dialect}
            onChange={(e) => setDialect(e.target.value)}
            className="w-full border border-[var(--line)] bg-[var(--ink-soft)] px-3 py-2 text-[var(--paper)]"
          >
            {(dialects.length
              ? dialects
              : [
                  { id: "sorani", label: "Sorani", script: "arabic" },
                  { id: "badini", label: "Badini", script: "arabic" },
                  { id: "kurmanji", label: "Kurmanji", script: "latin" },
                ]
            ).map((d) => (
              <option key={d.id} value={d.id}>
                {d.label}
              </option>
            ))}
          </select>
          <button
            type="submit"
            disabled={busy || !audioKey.trim()}
            className="border border-[var(--gold)] bg-[rgba(197,161,94,0.14)] px-4 py-2 text-xs uppercase tracking-[0.14em] text-[var(--gold-bright)] disabled:opacity-50"
          >
            {busy ? "Transcribing…" : "Transcribe"}
          </button>
        </form>
      </div>

      {recentJobs.length ? (
        <div className="mt-8 border border-[var(--line)] p-5">
          <p className="text-[0.7rem] uppercase tracking-[0.14em] text-[var(--mist)]">Recent jobs</p>
          <ul className="mt-3 flex flex-wrap gap-2">
            {recentJobs.map((id) => (
              <li key={id}>
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => void loadJob(id)}
                  className="border border-[var(--line)] px-3 py-1.5 font-mono text-xs text-[var(--paper-dim)] hover:border-[var(--gold)] hover:text-[var(--gold-bright)]"
                >
                  {id.slice(0, 8)}…
                </button>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {manifest ? (
        <div className="mt-10 border border-[var(--line)] p-5">
          <div className="flex flex-wrap items-baseline justify-between gap-3">
            <p className="text-[var(--paper)]">
              {manifest.engine}
              {manifest.model ? ` · ${manifest.model}` : ""} · {manifest.dialect} · avg conf{" "}
              {manifest.average_confidence} · {manifest.segment_count} segments · {manifest.status}
              {manifest.job_id ? (
                <span className="ml-2 font-mono text-xs text-[var(--mist)]">
                  job {manifest.job_id.slice(0, 8)}
                </span>
              ) : null}
            </p>
            {manifest.job_id ? (
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => void download("vtt")}
                  className="border border-[var(--line)] px-3 py-1.5 text-xs uppercase tracking-[0.12em] text-[var(--gold-bright)]"
                >
                  Download VTT
                </button>
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => void download("srt")}
                  className="border border-[var(--line)] px-3 py-1.5 text-xs uppercase tracking-[0.12em] text-[var(--gold-bright)]"
                >
                  Download SRT
                </button>
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => void download("json")}
                  className="border border-[var(--line)] px-3 py-1.5 text-xs uppercase tracking-[0.12em] text-[var(--paper-dim)]"
                >
                  Transcript JSON
                </button>
              </div>
            ) : null}
          </div>
          <ul className="mt-4 space-y-2">
            {manifest.segments.map((s, i) => (
              <li key={`${s.start}-${i}`} className="text-sm text-[var(--mist)]">
                <span className="text-[var(--paper-dim)]">
                  {s.start.toFixed(1)}–{s.end.toFixed(1)}s
                </span>{" "}
                {s.speaker}: {s.text}{" "}
                <span className="text-[var(--mist-soft)]">({s.confidence})</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </CoreShell>
  );
}
