"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { CoreShell } from "@/components/CoreShell";
import { VdNav } from "@/components/VdNav";
import { vdApi, type VdProject } from "@/lib/api";

export default function VdOverview() {
  const { vdId } = useParams<{ vdId: string }>();
  const [p, setP] = useState<VdProject | null>(null);
  const [err, setErr] = useState("");
  useEffect(() => {
    vdApi.get(vdId).then(setP).catch((e) => setErr(String(e.message || e)));
  }, [vdId]);
  return (
    <CoreShell title={p?.title || "AC Vertical Drama"} subtitle={p?.logline || p?.project_id || ""}>
      {p ? <VdNav vdId={p.id} projectId={p.project_id} /> : null}
      {err ? <p className="text-[var(--danger)]">{err}</p> : null}
      <p className="text-sm text-[var(--mist)]">Create a series. Build an IP. Produce episode by episode.</p>
      <p className="mt-4 text-sm">Locale: {p?.primary_locale} · Status: {p?.status}</p>
    </CoreShell>
  );
}
