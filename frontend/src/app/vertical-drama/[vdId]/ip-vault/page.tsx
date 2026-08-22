"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { CoreShell } from "@/components/CoreShell";
import { VdNav } from "@/components/VdNav";
import { vdApi, type VdProject } from "@/lib/api";

export default function IpVaultPage() {
  const { vdId } = useParams<{ vdId: string }>();
  const [p, setP] = useState<VdProject | null>(null);
  const [rights, setRights] = useState<Record<string, unknown>[]>([]);
  const [contrib, setContrib] = useState<Record<string, unknown>[]>([]);
  const [prov, setProv] = useState<Record<string, unknown>[]>([]);
  const [name, setName] = useState("");

  async function load() {
    const proj = await vdApi.get(vdId);
    setP(proj);
    setRights(await vdApi.rights(vdId));
    setContrib(await vdApi.contributors(vdId));
    setProv(await vdApi.provenance(vdId));
  }
  useEffect(() => {
    load().catch(() => undefined);
  }, [vdId]);

  return (
    <CoreShell title="IP Vault" subtitle={p?.title || ""}>
      {p ? <VdNav vdId={p.id} projectId={p.project_id} /> : null}
      <div className="mb-4 flex gap-2">
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Contributor" className="border border-[var(--line)] bg-transparent px-3 py-2" />
        <button
          type="button"
          onClick={() => vdApi.addContributor(vdId, { display_name: name || "Creator", role: "creator" }).then(load)}
          className="border border-[var(--gold)] px-3 py-2 text-[0.7rem] uppercase text-[var(--gold-bright)]"
        >
          Add
        </button>
        <button type="button" onClick={() => vdApi.addRights(vdId, { territory: "IQ", rights_type: "original" }).then(load)} className="border border-[var(--line)] px-3 py-2 text-[0.7rem] uppercase">
          Add rights
        </button>
      </div>
      <h3 className="mt-6 text-sm uppercase text-[var(--mist)]">Rights</h3>
      <pre className="mt-2 overflow-auto text-xs">{JSON.stringify(rights, null, 2)}</pre>
      <h3 className="mt-6 text-sm uppercase text-[var(--mist)]">Contributors</h3>
      <pre className="mt-2 overflow-auto text-xs">{JSON.stringify(contrib, null, 2)}</pre>
      <h3 className="mt-6 text-sm uppercase text-[var(--mist)]">Provenance</h3>
      <pre className="mt-2 overflow-auto text-xs">{JSON.stringify(prov, null, 2)}</pre>
    </CoreShell>
  );
}
