"use client";

import { useEffect, useState } from "react";
import { CoreShell } from "@/components/CoreShell";
import { api, type RegistryModel } from "@/lib/api";

export default function ModelsPage() {
  const [models, setModels] = useState<RegistryModel[]>([]);

  useEffect(() => {
    api.listRegistryModels().then(setModels).catch(() => undefined);
  }, []);

  return (
    <CoreShell
      title="Model Registry"
      subtitle="Official inventory of Art City foundation models, LoRAs, character adapters, and evaluation status."
    >
      <ul className="space-y-3">
        {models.map((m) => (
          <li key={m.id} className="border border-[var(--line)] px-4 py-4">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <p className="text-[var(--paper)]">
                {m.name} <span className="text-[var(--mist)]">{m.version}</span>
              </p>
              <span className="text-[0.7rem] uppercase tracking-[0.14em] text-[var(--gold)]">
                {m.status}
              </span>
            </div>
            <p className="mt-1 text-sm text-[var(--mist)]">
              {m.model_type} · {m.modality}
              {m.character_key ? ` · ${m.character_key}` : ""}
              {m.checksum ? ` · ${m.checksum.slice(0, 12)}…` : ""}
            </p>
          </li>
        ))}
        {!models.length ? <p className="text-[var(--mist)]">No models registered.</p> : null}
      </ul>
    </CoreShell>
  );
}
