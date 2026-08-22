"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { CoreShell } from "@/components/CoreShell";
import { useLocale } from "@/components/LocaleProvider";
import { vdApi, type VdProject } from "@/lib/api";

export default function VerticalDramaHome() {
  const { t } = useLocale();
  const router = useRouter();
  const [rows, setRows] = useState<VdProject[]>([]);
  const [title, setTitle] = useState("New Vertical Drama");
  const [logline, setLogline] = useState("");
  const [locale, setLoc] = useState("en");
  const [status, setStatus] = useState("");
  const [enabled, setEnabled] = useState(true);

  useEffect(() => {
    vdApi
      .features()
      .then((f) => {
        setEnabled(f.enabled);
        if (f.enabled) return vdApi.list().then(setRows);
      })
      .catch((e) => setStatus(String(e.message || e)));
  }, []);

  async function create(seed = false) {
    setStatus("Creating…");
    const p = await vdApi.create({
      title,
      logline,
      source_type: seed ? "generate" : "idea",
      primary_locale: locale,
      content_languages: locale === "ckb-IQ" ? ["ckb-IQ", "en"] : ["en"],
      seed_golden_a: seed,
    });
    router.push(`/vertical-drama/${p.id}`);
  }

  return (
    <CoreShell title={t("vd.title")} subtitle={t("vd.subtitle")}>
      {!enabled ? <p className="text-[var(--danger)]">Vertical Drama is not entitled.</p> : null}
      {status ? <p className="mb-4 text-sm text-[var(--mist)]">{status}</p> : null}
      <div className="mb-8 grid gap-3 md:grid-cols-2">
        <input value={title} onChange={(e) => setTitle(e.target.value)} className="border border-[var(--line)] bg-transparent px-3 py-2" />
        <select value={locale} onChange={(e) => setLoc(e.target.value)} className="border border-[var(--line)] bg-transparent px-3 py-2">
          <option value="en">English</option>
          <option value="ckb-IQ">کوردی سۆرانی</option>
          <option value="ar">Arabic</option>
        </select>
        <textarea value={logline} onChange={(e) => setLogline(e.target.value)} rows={2} placeholder="Logline / idea…" className="md:col-span-2 border border-[var(--line)] bg-transparent px-3 py-2" dir="auto" />
        <button type="button" onClick={() => create(false).catch((e) => setStatus(String(e.message || e)))} className="border border-[var(--gold)] px-3 py-2 text-[0.7rem] uppercase text-[var(--gold-bright)]">
          {t("vd.newProject")}
        </button>
        <button type="button" onClick={() => create(true).catch((e) => setStatus(String(e.message || e)))} className="border border-[var(--line)] px-3 py-2 text-[0.7rem] uppercase">
          {t("vd.goldenA")}
        </button>
      </div>
      <div className="grid gap-3">
        {rows.map((r) => (
          <Link key={r.id} href={`/vertical-drama/${r.id}`} className="border border-[var(--line)] px-4 py-4 hover:border-[var(--gold)]">
            <p className="text-[var(--paper)]">{r.title}</p>
            <p className="text-[0.75rem] text-[var(--mist)]">{r.project_id}</p>
          </Link>
        ))}
      </div>
    </CoreShell>
  );
}
