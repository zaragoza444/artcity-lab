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
      subtitle="Cinema · Studio · Vertical Drama · Graphic Motion · Edit · Hub · Publish — with Model Gateway, Data Lab, and owned inference control."
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
          ["/vertical-drama", "Vertical Drama", "IP Factory · bible · episodes · 9:16"],
          ["/graphic-motion", "Graphic Motion", "MSG · Sorani/RTL · preview · broadcast"],
          ["/hub", "Production Hub", "AC Script · breakdown · handoff"],
          ["/cinema", "Cinema", "Complete advertising campaigns"],
          ["/studio", "Studio", "Individual production assets"],
          ["/data-bank", "Data Bank", "Project media vault · upload · sync"],
          ["/edit", "Edit", "Long-form to social clips"],
          ["/publish", "Publish", "Masters · QC · release"],
        ].map(([href, label, blurb]) => (
          <Link
            key={href}
            href={href}
            className="border border-[var(--line)] px-4 py-5 transition hover:border-[var(--gold)]"
          >
            <p className="text-sm uppercase tracking-[0.14em] text-[var(--gold-bright)]">{label}</p>
            <p className="mt-2 text-[0.8rem] leading-snug text-[var(--mist)]">{blurb}</p>
          </Link>
        ))}
      </div>
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          ["/data-lab", "Data Lab"],
          ["/data-lab/annotations", "Annotations"],
          ["/models", "Models"],
          ["/training", "Training"],
          ["/knowledge", "Knowledge"],
          ["/speech", "Speech"],
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
