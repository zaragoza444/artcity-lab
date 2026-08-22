"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { CoreShell } from "@/components/CoreShell";
import { useLocale } from "@/components/LocaleProvider";
import { hubApi, type HubScript, type HubScriptVersion } from "@/lib/api";

export default function HubScriptVersionsPage() {
  const params = useParams<{ projectId: string }>();
  const projectId = params.projectId;
  const { t } = useLocale();
  const [scripts, setScripts] = useState<HubScript[]>([]);
  const [scriptId, setScriptId] = useState("");
  const [versions, setVersions] = useState<HubScriptVersion[]>([]);
  const [a, setA] = useState("");
  const [b, setB] = useState("");
  const [diff, setDiff] = useState<{ left: string[]; right: string[]; added: number; removed: number } | null>(null);
  const [status, setStatus] = useState("");

  useEffect(() => {
    hubApi
      .listScripts(projectId)
      .then(async (list) => {
        setScripts(list);
        if (list[0]) {
          setScriptId(list[0].id);
          const vs = await hubApi.listVersions(list[0].id);
          setVersions(vs);
          if (vs[1]) setA(vs[1].id);
          if (vs[0]) setB(vs[0].id);
        }
      })
      .catch((e) => setStatus(String(e.message || e)));
  }, [projectId]);

  async function loadVersions(id: string) {
    setScriptId(id);
    const vs = await hubApi.listVersions(id);
    setVersions(vs);
    setA(vs[1]?.id || "");
    setB(vs[0]?.id || "");
    setDiff(null);
  }

  async function compare() {
    if (!a || !b) return;
    const res = await hubApi.compareVersions(a, b);
    setDiff(res);
  }

  async function lock(id: string) {
    const v = await hubApi.lockVersion(id);
    setVersions((prev) => prev.map((x) => (x.id === id ? v : x)));
    setStatus(t("script.lock") + " ✓");
  }

  return (
    <CoreShell title={t("script.compare")} subtitle={projectId}>
      <div className="mb-4 flex flex-wrap gap-2">
        <Link href={`/hub/${projectId}/script`} className="border border-[var(--line)] px-3 py-2 text-[0.7rem] uppercase">
          {t("hub.script")}
        </Link>
        <select
          value={scriptId}
          onChange={(e) => loadVersions(e.target.value).catch((err) => setStatus(String(err.message || err)))}
          className="border border-[var(--line)] bg-transparent px-2 py-2"
        >
          {scripts.map((s) => (
            <option key={s.id} value={s.id}>
              {s.title}
            </option>
          ))}
        </select>
      </div>

      <div className="mb-4 overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="text-[0.65rem] uppercase tracking-[0.12em] text-[var(--mist)]">
              <th className="py-2">Label</th>
              <th>Status</th>
              <th>Pages</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {versions.map((v) => (
              <tr key={v.id} className="border-t border-[var(--line)]">
                <td className="py-2">{v.version_label}</td>
                <td>{v.status}</td>
                <td>{(v.page_eighths / 8).toFixed(2)}</td>
                <td>
                  {v.status !== "locked" ? (
                    <button
                      type="button"
                      onClick={() => lock(v.id).catch((e) => setStatus(String(e.message || e)))}
                      className="text-[0.7rem] uppercase text-[var(--gold-bright)]"
                    >
                      {t("script.lock")}
                    </button>
                  ) : (
                    <span className="text-[var(--danger)]">{t("script.locked")}</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mb-4 flex flex-wrap gap-2">
        <select value={a} onChange={(e) => setA(e.target.value)} className="border border-[var(--line)] bg-transparent px-2 py-2">
          <option value="">Version A</option>
          {versions.map((v) => (
            <option key={v.id} value={v.id}>
              {v.version_label}
            </option>
          ))}
        </select>
        <select value={b} onChange={(e) => setB(e.target.value)} className="border border-[var(--line)] bg-transparent px-2 py-2">
          <option value="">Version B</option>
          {versions.map((v) => (
            <option key={v.id} value={v.id}>
              {v.version_label}
            </option>
          ))}
        </select>
        <button
          type="button"
          onClick={() => compare().catch((e) => setStatus(String(e.message || e)))}
          className="border border-[var(--gold)] px-3 py-2 text-[0.7rem] uppercase text-[var(--gold-bright)]"
        >
          {t("script.compare")}
        </button>
      </div>

      {diff ? (
        <div className="grid gap-4 md:grid-cols-2">
          <pre className="overflow-auto border border-[var(--line)] p-3 text-xs whitespace-pre-wrap">{diff.left.join("\n")}</pre>
          <pre className="overflow-auto border border-[var(--line)] p-3 text-xs whitespace-pre-wrap">{diff.right.join("\n")}</pre>
          <p className="text-sm text-[var(--mist)] md:col-span-2">
            +{diff.added} / −{diff.removed}
          </p>
        </div>
      ) : null}
      {status ? <p className="mt-3 text-sm text-[var(--mist)]">{status}</p> : null}
    </CoreShell>
  );
}
