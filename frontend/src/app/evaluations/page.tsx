"use client";

import { useEffect, useState } from "react";
import { CoreShell } from "@/components/CoreShell";
import { api, type EvaluationRun } from "@/lib/api";

export default function EvaluationsPage() {
  const [runs, setRuns] = useState<EvaluationRun[]>([]);

  useEffect(() => {
    api.listEvaluations().then(setRuns).catch(() => undefined);
  }, []);

  return (
    <CoreShell
      title="Evaluations"
      subtitle="No candidate model replaces production without benchmark comparison and human approval."
    >
      <ul className="space-y-3">
        {runs.map((r) => (
          <li key={r.id} className="border border-[var(--line)] px-4 py-4">
            <p className="text-[var(--paper)]">{r.modality} evaluation</p>
            <p className="mt-1 text-sm text-[var(--mist)]">
              {r.status}
              {r.human_decision ? ` · ${r.human_decision}` : ""}
            </p>
          </li>
        ))}
        {!runs.length ? <p className="text-[var(--mist)]">No evaluation runs yet.</p> : null}
      </ul>
    </CoreShell>
  );
}
