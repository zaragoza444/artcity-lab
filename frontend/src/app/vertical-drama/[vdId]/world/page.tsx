"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { CoreShell } from "@/components/CoreShell";
import { VdNav } from "@/components/VdNav";
import { vdApi, type VdProject } from "@/lib/api";

export default function WorldPage() {
  const { vdId } = useParams<{ vdId: string }>();
  const [p, setP] = useState<VdProject | null>(null);
  const [chars, setChars] = useState<Record<string, unknown>[]>([]);
  const [locs, setLocs] = useState<Record<string, unknown>[]>([]);
  const [canon, setCanon] = useState<Record<string, unknown>[]>([]);
  const [name, setName] = useState("");
  const [key, setKey] = useState("rule");
  const [value, setValue] = useState("");

  async function load() {
    const proj = await vdApi.get(vdId);
    setP(proj);
    setChars(await vdApi.characters(vdId));
    setLocs(await vdApi.locations(vdId));
    setCanon(await vdApi.canon(vdId));
  }
  useEffect(() => {
    load().catch(() => undefined);
  }, [vdId]);

  return (
    <CoreShell title="Story World" subtitle={p?.title || ""}>
      {p ? <VdNav vdId={p.id} projectId={p.project_id} /> : null}
      <div className="mb-4 flex flex-wrap gap-2">
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Character / location" className="border border-[var(--line)] bg-transparent px-3 py-2" dir="auto" />
        <button type="button" onClick={() => vdApi.addCharacter(vdId, { display_name: name, identity_locked: true, locale: p?.primary_locale }).then(load)} className="border border-[var(--gold)] px-3 py-2 text-[0.7rem] uppercase text-[var(--gold-bright)]">
          Character
        </button>
        <button type="button" onClick={() => vdApi.addLocation(vdId, { display_name: name, locale: p?.primary_locale }).then(load)} className="border border-[var(--line)] px-3 py-2 text-[0.7rem] uppercase">
          Location
        </button>
      </div>
      <div className="mb-6 flex flex-wrap gap-2">
        <input value={key} onChange={(e) => setKey(e.target.value)} className="border border-[var(--line)] bg-transparent px-3 py-2" />
        <input value={value} onChange={(e) => setValue(e.target.value)} className="border border-[var(--line)] bg-transparent px-3 py-2" dir="auto" />
        <button type="button" onClick={() => vdApi.addCanon(vdId, { fact_key: key, fact_value: value }).then(load)} className="border border-[var(--line)] px-3 py-2 text-[0.7rem] uppercase">
          Canon fact
        </button>
      </div>
      <div className="grid gap-6 md:grid-cols-2">
        <div>
          <h3 className="text-sm uppercase text-[var(--mist)]">Characters</h3>
          <ul className="mt-2 text-sm">{chars.map((c) => <li key={String(c.id)}>{String(c.display_name)} {c.identity_locked ? "· locked" : ""}</li>)}</ul>
        </div>
        <div>
          <h3 className="text-sm uppercase text-[var(--mist)]">Locations</h3>
          <ul className="mt-2 text-sm">{locs.map((c) => <li key={String(c.id)}>{String(c.display_name)}</li>)}</ul>
        </div>
      </div>
      <h3 className="mt-8 text-sm uppercase text-[var(--mist)]">Canon</h3>
      <ul className="mt-2 space-y-2 text-sm">
        {canon.map((c) => (
          <li key={String(c.id)} className="flex gap-2">
            <span>{String(c.fact_key)} = {String(c.fact_value)} ({String(c.status)})</span>
            {c.status !== "locked" ? (
              <button type="button" onClick={() => vdApi.approveCanon(String(c.id)).then(load)} className="text-[var(--teal)]">
                Lock
              </button>
            ) : null}
          </li>
        ))}
      </ul>
    </CoreShell>
  );
}
