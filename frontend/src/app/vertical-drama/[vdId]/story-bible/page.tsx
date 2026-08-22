"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { CoreShell } from "@/components/CoreShell";
import { VdNav } from "@/components/VdNav";
import { vdApi, type VdProject } from "@/lib/api";

export default function BiblePage() {
  const { vdId } = useParams<{ vdId: string }>();
  const [p, setP] = useState<VdProject | null>(null);
  const [bible, setBible] = useState<Record<string, unknown> | null>(null);
  const [world, setWorld] = useState("Serialized vertical drama. Canon is locked after approval.");
  const [tone, setTone] = useState("Intimate, high-stakes, 9:16 close-ups.");

  async function load() {
    setP(await vdApi.get(vdId));
    setBible(await vdApi.bible(vdId));
  }
  useEffect(() => {
    load().catch(() => undefined);
  }, [vdId]);

  const current = (bible?.current || {}) as Record<string, unknown>;
  const versionId = current.id as string | undefined;

  return (
    <CoreShell title="Story Bible" subtitle={p?.title || ""}>
      {p ? <VdNav vdId={p.id} projectId={p.project_id} /> : null}
      <textarea value={world} onChange={(e) => setWorld(e.target.value)} rows={4} className="mb-3 w-full border border-[var(--line)] bg-transparent px-3 py-2" dir="auto" />
      <textarea value={tone} onChange={(e) => setTone(e.target.value)} rows={2} className="mb-3 w-full border border-[var(--line)] bg-transparent px-3 py-2" dir="auto" />
      <div className="flex gap-2">
        <button type="button" onClick={() => vdApi.saveBible(vdId, { world, tone, language: p?.primary_locale }).then(load)} className="border border-[var(--gold)] px-3 py-2 text-[0.7rem] uppercase text-[var(--gold-bright)]">
          Save version
        </button>
        {versionId ? (
          <button type="button" onClick={() => vdApi.approveBible(versionId).then(load)} className="border border-[var(--line)] px-3 py-2 text-[0.7rem] uppercase">
            Approve / lock
          </button>
        ) : null}
      </div>
      <pre className="mt-6 overflow-auto text-xs">{JSON.stringify(bible, null, 2)}</pre>
    </CoreShell>
  );
}
