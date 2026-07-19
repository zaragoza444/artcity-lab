"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { CoreShell } from "@/components/CoreShell";
import { api, type Dataset } from "@/lib/api";

export default function DataLabPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.listDatasets().then(setDatasets).catch((e) => setError(String(e.message || e)));
  }, []);

  return (
    <CoreShell
      title="Data Lab"
      subtitle="Datasets for training, fine-tuning, LoRA, evaluation, and Kurdish cultural archives. Upload is not training — rights and review required."
    >
      <div className="mb-6 flex gap-4">
        <Link
          href="/data-lab/annotations"
          className="border border-[var(--line)] px-4 py-2 text-xs uppercase tracking-[0.14em] text-[var(--paper-dim)]"
        >
          Annotations
        </Link>
      </div>
      {error ? <p className="text-[var(--danger)]">{error}</p> : null}
      <ul className="space-y-3">
        {datasets.map((d) => (
          <li key={d.id} className="border border-[var(--line)] px-4 py-4">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <p className="text-[var(--paper)]">{d.name}</p>
              <span className="text-[0.7rem] uppercase tracking-[0.14em] text-[var(--teal)]">
                {d.status}
              </span>
            </div>
            <p className="mt-1 text-sm text-[var(--mist)]">
              {d.category} · {d.media_type} · v{d.version} · {d.record_count} records
              {d.ai_training_permission ? " · AI training permitted" : ""}
            </p>
          </li>
        ))}
        {!datasets.length && !error ? (
          <p className="text-[var(--mist)]">No datasets yet. Seed AI Core or ingest via API.</p>
        ) : null}
      </ul>
    </CoreShell>
  );
}
