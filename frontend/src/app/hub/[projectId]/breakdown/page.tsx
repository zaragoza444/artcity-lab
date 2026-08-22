"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { CoreShell } from "@/components/CoreShell";
import { useLocale } from "@/components/LocaleProvider";
import { hubApi, type HubBreakdownItem, type HubScene, type HubScript, type HubScriptVersion } from "@/lib/api";

export default function HubBreakdownPage() {
  const params = useParams<{ projectId: string }>();
  const projectId = params.projectId;
  const { t } = useLocale();
  const [scripts, setScripts] = useState<HubScript[]>([]);
  const [version, setVersion] = useState<HubScriptVersion | null>(null);
  const [scenes, setScenes] = useState<HubScene[]>([]);
  const [items, setItems] = useState<HubBreakdownItem[]>([]);
  const [status, setStatus] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const list = await hubApi.listScripts(projectId);
        setScripts(list);
        const s = list[0];
        if (!s) return;
        const vs = await hubApi.listVersions(s.id);
        const current = vs.find((v) => v.id === s.current_version_id) || vs[0];
        if (!current) return;
        setVersion(current);
        setScenes(await hubApi.listScenes(current.id).catch(() => []));
        setItems(await hubApi.listBreakdown(current.id));
      } catch (e) {
        setStatus(String((e as Error).message || e));
      }
    })();
  }, [projectId]);

  async function propose() {
    if (!version) return;
    const proposed = await hubApi.proposeBreakdown(version.id);
    setItems(proposed);
    setStatus(`${t("breakdown.propose")}: ${proposed.length}`);
  }

  async function decide(id: string, decision: "approved" | "rejected") {
    const updated = await hubApi.decideBreakdown(id, decision);
    setItems((prev) => prev.map((i) => (i.id === id ? updated : i)));
  }

  return (
    <CoreShell title={t("hub.breakdown")} subtitle={version?.version_label || projectId}>
      <div className="mb-4 flex flex-wrap gap-2">
        <Link href={`/hub/${projectId}/script`} className="border border-[var(--line)] px-3 py-2 text-[0.7rem] uppercase">
          {t("hub.script")}
        </Link>
        <button
          type="button"
          disabled={!version}
          onClick={() => propose().catch((e) => setStatus(String(e.message || e)))}
          className="border border-[var(--gold)] px-3 py-2 text-[0.7rem] uppercase text-[var(--gold-bright)] disabled:opacity-40"
        >
          {t("breakdown.propose")}
        </button>
      </div>

      {!scripts.length ? <p className="text-[var(--mist)]">Create a script first.</p> : null}

      <div className="mb-6 text-sm text-[var(--mist)]">
        Scenes: {scenes.length} · Items: {items.length}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="text-[0.65rem] uppercase tracking-[0.12em] text-[var(--mist)]">
              <th className="py-2">{t("breakdown.category")}</th>
              <th>Name</th>
              <th>{t("breakdown.status")}</th>
              <th>Source</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id} className="border-t border-[var(--line)]">
                <td className="py-2">{item.category}</td>
                <td>{item.display_text}</td>
                <td>{item.approval_status}</td>
                <td>{item.source}</td>
                <td className="space-x-2">
                  {item.approval_status === "proposed" ? (
                    <>
                      <button
                        type="button"
                        onClick={() => decide(item.id, "approved").catch((e) => setStatus(String(e.message || e)))}
                        className="text-[0.7rem] uppercase text-[var(--teal)]"
                      >
                        {t("breakdown.approve")}
                      </button>
                      <button
                        type="button"
                        onClick={() => decide(item.id, "rejected").catch((e) => setStatus(String(e.message || e)))}
                        className="text-[0.7rem] uppercase text-[var(--danger)]"
                      >
                        {t("breakdown.reject")}
                      </button>
                    </>
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {status ? <p className="mt-3 text-sm text-[var(--mist)]">{status}</p> : null}
    </CoreShell>
  );
}
