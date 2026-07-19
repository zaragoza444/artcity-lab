"use client";

import { useEffect, useState } from "react";
import { CoreShell } from "@/components/CoreShell";
import { api, type TrainingJob } from "@/lib/api";

export default function TrainingPage() {
  const [jobs, setJobs] = useState<TrainingJob[]>([]);

  useEffect(() => {
    api.listTraining().then(setJobs).catch(() => undefined);
  }, []);

  return (
    <CoreShell
      title="Training"
      subtitle="LoRA and parameter-efficient adaptation. Datasets must be training_ready with approved rights before a job can start."
    >
      <ul className="space-y-3">
        {jobs.map((j) => (
          <li key={j.id} className="border border-[var(--line)] px-4 py-4">
            <p className="text-[var(--paper)]">{j.base_model}</p>
            <p className="mt-1 text-sm text-[var(--mist)]">
              {j.status} · epochs {j.epochs}
              {j.resulting_model_id ? ` · model ${j.resulting_model_id.slice(0, 8)}` : ""}
            </p>
          </li>
        ))}
        {!jobs.length ? (
          <p className="text-[var(--mist)]">
            No training jobs yet. Create via API after rights-gated datasets are ready.
          </p>
        ) : null}
      </ul>
    </CoreShell>
  );
}
