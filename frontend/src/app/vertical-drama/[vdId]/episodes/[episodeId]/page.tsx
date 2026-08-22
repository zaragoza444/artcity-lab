"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { CoreShell } from "@/components/CoreShell";
import { VdNav } from "@/components/VdNav";
import { vdApi, type VdProject } from "@/lib/api";

export default function EpisodePage() {
  const { vdId, episodeId } = useParams<{ vdId: string; episodeId: string }>();
  const [p, setP] = useState<VdProject | null>(null);
  const [ep, setEp] = useState<Record<string, unknown> | null>(null);
  const [status, setStatus] = useState("");
  const [script, setScript] = useState("INT. ROOM - DAY\nShe waits.\n\nHERO\nWe finish this tonight.");

  async function load() {
    setP(await vdApi.get(vdId));
    const data = await vdApi.episode(episodeId);
    setEp(data);
  }
  useEffect(() => {
    load().catch((e) => setStatus(String(e.message || e)));
  }, [vdId, episodeId]);

  async function saveScript() {
    const elements = script.split("\n").filter(Boolean).map((line) => {
      if (line.startsWith("INT.") || line.startsWith("EXT.")) return { element_type: "scene_heading", display_text: line };
      if (line === line.toUpperCase() && line.length < 40) return { element_type: "character", display_text: line };
      return { element_type: "action", display_text: line };
    });
    await vdApi.saveScreenplay(episodeId, { title: ep?.title, elements });
    await load();
    setStatus("Screenplay saved");
  }

  return (
    <CoreShell title={String(ep?.title || "Episode")} subtitle={String(ep?.status || "")}>
      {p ? <VdNav vdId={p.id} projectId={p.project_id} /> : null}
      {ep?.stale ? <p className="mb-3 border border-[var(--danger)] px-3 py-2 text-sm text-[var(--danger)]">{String(ep.stale_reason)}</p> : null}
      <div className="mb-4 flex flex-wrap gap-2">
        {["drafted", "reviewed", "approved", "production_ready", "locked"].map((s) => (
          <button key={s} type="button" onClick={() => vdApi.patchEpisode(episodeId, { status: s }).then(load).catch((e) => setStatus(String(e.message || e)))} className="border border-[var(--line)] px-2 py-1 text-[0.65rem] uppercase">
            {s}
          </button>
        ))}
      </div>
      <textarea value={script} onChange={(e) => setScript(e.target.value)} rows={8} className="w-full border border-[var(--line)] bg-transparent px-3 py-2 text-sm" dir="auto" />
      <div className="mt-3 flex flex-wrap gap-2">
        <button type="button" onClick={() => saveScript().catch((e) => setStatus(String(e.message || e)))} className="border border-[var(--gold)] px-3 py-2 text-[0.7rem] uppercase text-[var(--gold-bright)]">
          Save screenplay
        </button>
        <button type="button" onClick={() => vdApi.decoupage(episodeId).then(load).catch((e) => setStatus(String(e.message || e)))} className="border border-[var(--line)] px-3 py-2 text-[0.7rem] uppercase">
          Découpage
        </button>
        <button type="button" onClick={() => vdApi.qc(episodeId).then((r) => setStatus(JSON.stringify(r))).catch((e) => setStatus(String(e.message || e)))} className="border border-[var(--line)] px-3 py-2 text-[0.7rem] uppercase">
          QC
        </button>
        <button type="button" onClick={() => vdApi.assemble(episodeId).then((r) => setStatus(JSON.stringify(r))).catch((e) => setStatus(String(e.message || e)))} className="border border-[var(--teal)] px-3 py-2 text-[0.7rem] uppercase text-[var(--teal)]">
          Handoff Edit
        </button>
        <button
          type="button"
          onClick={() =>
            vdApi.localize(episodeId, { language: "ckb-IQ", kind: "subtitle", body: String(ep?.hook || "") }).then(load)
          }
          className="border border-[var(--line)] px-3 py-2 text-[0.7rem] uppercase"
        >
          Sorani subtitle
        </button>
        <button type="button" onClick={() => vdApi.delivery(episodeId).then((r) => setStatus(JSON.stringify(r))).catch((e) => setStatus(String(e.message || e)))} className="border border-[var(--gold)] px-3 py-2 text-[0.7rem] uppercase">
          Delivery package
        </button>
      </div>
      <div className="mt-6 space-y-2">
        {((ep?.shots as Record<string, unknown>[]) || []).map((s) => (
          <div key={String(s.id)} className="flex items-center justify-between border border-[var(--line)] px-3 py-2 text-sm">
            <span>
              Shot {String(s.shot_number)} · {String(s.framing)} · {String(s.status)}
            </span>
            <button type="button" onClick={() => vdApi.generateShot(String(s.id)).then(load)} className="text-[0.7rem] uppercase text-[var(--gold-bright)]">
              Generate
            </button>
          </div>
        ))}
      </div>
      {status ? <p className="mt-4 whitespace-pre-wrap text-xs text-[var(--mist)]">{status}</p> : null}
    </CoreShell>
  );
}
