"use client";

import { useEffect, useState } from "react";
import { CoreShell } from "@/components/CoreShell";
import { api, type RightsRecord } from "@/lib/api";

export default function RightsPage() {
  const [rows, setRows] = useState<RightsRecord[]>([]);

  useEffect(() => {
    api.listRights().then(setRows).catch(() => undefined);
  }, []);

  return (
    <CoreShell
      title="Rights"
      subtitle="Traceable rights and consent before commercial use or model training. Backend blocks training without approved AI-training rights."
    >
      <ul className="space-y-3">
        {rows.map((r) => (
          <li key={r.id} className="border border-[var(--line)] px-4 py-4">
            <p className="text-[var(--paper)]">{r.copyright_owner}</p>
            <p className="mt-1 text-sm text-[var(--mist)]">
              {r.legal_status}
              {r.ai_training ? " · AI training" : ""}
              {r.commercial_use ? " · commercial" : ""}
            </p>
          </li>
        ))}
        {!rows.length ? <p className="text-[var(--mist)]">No rights records yet.</p> : null}
      </ul>
    </CoreShell>
  );
}
