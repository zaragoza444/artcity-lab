"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { CoreShell } from "@/components/CoreShell";
import { api } from "@/lib/api";

export default function DashboardPage() {
  const [providers, setProviders] = useState<{ name: string; healthy: boolean }[]>([]);
  const [models, setModels] = useState(0);
  const [datasets, setDatasets] = useState(0);

  useEffect(() => {
    Promise.all([api.listProviders(), api.listRegistryModels(), api.listDatasets()])
      .then(([p, m, d]) => {
        setProviders(p);
        setModels(m.length);
        setDatasets(d.length);
      })
      .catch(() => undefined);
  }, []);

  return (
    <CoreShell
      title="Dashboard"
      subtitle="Art City production OS with Model Gateway, Data Lab, and owned inference control."
    >
      <div className="grid gap-6 md:grid-cols-3">
        <Stat label="Registered models" value={String(models)} />
        <Stat label="Datasets" value={String(datasets)} />
        <Stat
          label="Providers healthy"
          value={`${providers.filter((p) => p.healthy).length}/${providers.length || 0}`}
        />
      </div>
      <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          ["/cinema", "Cinema"],
          ["/studio", "Studio"],
          ["/data-lab", "Data Lab"],
          ["/models", "Models"],
          ["/training", "Training"],
          ["/knowledge", "Knowledge"],
          ["/rights", "Rights"],
          ["/evaluations", "Evaluations"],
        ].map(([href, label]) => (
          <Link
            key={href}
            href={href}
            className="border border-[var(--line)] px-4 py-5 text-sm uppercase tracking-[0.14em] text-[var(--paper-dim)] transition hover:border-[var(--gold)] hover:text-[var(--gold-bright)]"
          >
            {label}
          </Link>
        ))}
      </div>
    </CoreShell>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-[var(--line)] px-5 py-6">
      <p className="text-[0.7rem] uppercase tracking-[0.16em] text-[var(--mist)]">{label}</p>
      <p className="mt-3 font-[family-name:var(--font-display)] text-3xl text-[var(--paper)]">
        {value}
      </p>
    </div>
  );
}
