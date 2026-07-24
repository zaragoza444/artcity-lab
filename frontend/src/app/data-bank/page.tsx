"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type DataBankHub, type DataBankSeed } from "@/lib/api";
import { PageHeader } from "@/components/PageHeader";
import { SiteHeader } from "@/components/SiteHeader";

export default function DataBankHubPage() {
  const [hub, setHub] = useState<DataBankHub | null>(null);
  const [seed, setSeed] = useState<DataBankSeed | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      setHub(await api.dataBankHub());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load data bank");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function onSeed() {
    setBusy(true);
    setError(null);
    try {
      const result = await api.seedDataBank();
      setSeed(result);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Seed failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="min-h-screen pb-20">
      <SiteHeader />
      <div className="ac-container pt-10 md:pt-14">
        <PageHeader
          eyebrow="Art City Data Bank"
          title="Project media vault"
          description="Browse, upload, and sync production assets for every project — Studio generations, stills, and reference files in one bank."
          actions={
            <button type="button" className="ac-btn ac-btn-primary" disabled={busy} onClick={() => void onSeed()}>
              {busy ? "Seeding…" : "Seed bank + bank building still"}
            </button>
          }
        />

        {loading ? (
          <p className="text-[0.8rem] tracking-[0.18em] text-[var(--mist)] uppercase">Opening vault…</p>
        ) : error ? (
          <p className="text-[var(--danger)]">{error}</p>
        ) : (
          <>
            <div className="mb-10 grid gap-4 sm:grid-cols-3">
              <Stat label="Projects with assets" value={String(hub?.projects_with_assets ?? 0)} />
              <Stat label="Total bank assets" value={String(hub?.total_assets ?? 0)} />
              <Stat
                label="Central bank"
                value={hub?.bank_project_id ? "Ready" : "Not seeded"}
              />
            </div>

            {seed ? (
              <p className="mb-8 text-sm text-[var(--mist-soft)]">
                Seeded project <span className="text-[var(--gold)]">{seed.project.name}</span> · job{" "}
                {seed.seed_status} · assets {seed.summary.total}
                {seed.project.id ? (
                  <>
                    {" · "}
                    <Link
                      href={`/projects/${seed.project.id}/data-bank`}
                      className="text-[var(--gold)]"
                    >
                      Open bank →
                    </Link>
                  </>
                ) : null}
              </p>
            ) : null}

            {!hub?.projects.length ? (
              <p className="text-sm text-[var(--mist)]">
                No project assets yet. Seed the central bank or open a project and upload files.
              </p>
            ) : (
              <ul className="border-t border-[var(--line)]">
                {hub.projects.map((p) => (
                  <li key={p.project_id} className="ac-row">
                    <Link
                      href={`/projects/${p.project_id}/data-bank`}
                      className="group grid grid-cols-[1fr_auto] items-baseline gap-4 py-6"
                    >
                      <div>
                        <p className="ac-display text-2xl tracking-tight transition group-hover:text-[var(--gold-bright)]">
                          {p.name}
                        </p>
                        <p className="mt-2 text-[0.72rem] tracking-[0.16em] text-[var(--mist-soft)] uppercase">
                          {p.total} assets · {Object.keys(p.by_type).join(" · ") || "mixed"}
                        </p>
                      </div>
                      <span className="ac-display text-[0.68rem] tracking-[0.18em] text-[var(--gold)] uppercase">
                        Enter →
                      </span>
                    </Link>
                    <div className="ac-rule" />
                  </li>
                ))}
              </ul>
            )}

            {hub?.bank_project_id ? (
              <p className="mt-10">
                <Link
                  href={`/projects/${hub.bank_project_id}/data-bank`}
                  className="ac-btn ac-btn-primary"
                >
                  Open Art City Data Bank project
                </Link>
              </p>
            ) : null}
          </>
        )}
      </div>
    </main>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-[var(--line)] bg-[rgba(10,15,22,0.35)] px-5 py-5">
      <p className="ac-display text-[0.68rem] tracking-[0.18em] text-[var(--mist)] uppercase">{label}</p>
      <p className="ac-display mt-2 text-3xl tracking-tight text-[var(--paper)]">{value}</p>
    </div>
  );
}
