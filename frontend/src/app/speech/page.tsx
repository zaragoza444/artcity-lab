"use client";

import { FormEvent, useEffect, useState } from "react";
import { CoreShell } from "@/components/CoreShell";
import { api, type AsrManifest, type SpeechDialect } from "@/lib/api";

export default function SpeechPage() {
  const [dialects, setDialects] = useState<SpeechDialect[]>([]);
  const [model, setModel] = useState("AC-KURDISH-ASR-v1");
  const [dialect, setDialect] = useState("sorani");
  const [audioKey, setAudioKey] = useState("projects/pilot/voice/sample.wav");
  const [detectText, setDetectText] = useState("Silav, Newroz û Zagros");
  const [detection, setDetection] = useState<string | null>(null);
  const [manifest, setManifest] = useState<AsrManifest | null>(null);
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
  }, []);

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

  async function onAsr(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const r = await api.runAsr({
        audio_storage_key: audioKey,
        dialect,
        duration_hint: 9,
      });
      setManifest(r);
    } catch (err) {
      setError(err instanceof Error ? err.message : "ASR failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <CoreShell
      title="Kurdish Speech"
      subtitle={`${model} pilot — Sorani, Badini, and Kurmanji ASR, detection, and subtitle prep.`}
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
            Run ASR pilot
          </p>
          <input
            value={audioKey}
            onChange={(e) => setAudioKey(e.target.value)}
            className="w-full border border-[var(--line)] bg-[var(--ink-soft)] px-3 py-2 text-[var(--paper)]"
            placeholder="audio storage key"
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
            disabled={busy}
            className="border border-[var(--gold)] bg-[rgba(197,161,94,0.14)] px-4 py-2 text-xs uppercase tracking-[0.14em] text-[var(--gold-bright)]"
          >
            {busy ? "Transcribing…" : "Transcribe"}
          </button>
        </form>
      </div>

      {manifest ? (
        <div className="mt-10 border border-[var(--line)] p-5">
          <p className="text-[var(--paper)]">
            {manifest.engine} · {manifest.dialect} · avg conf {manifest.average_confidence} ·{" "}
            {manifest.segment_count} segments · {manifest.status}
          </p>
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
