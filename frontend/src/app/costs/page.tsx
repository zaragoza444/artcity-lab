"use client";

import { CoreShell } from "@/components/CoreShell";

export default function CostsPage() {
  return (
    <CoreShell
      title="Costs"
      subtitle="Gateway jobs record estimated and actual provider cost per generation. Project budgets remain enforced in Studio."
    >
      <p className="text-[var(--mist)]">
        Cost records are written on every Model Gateway completion. Open a project Studio summary for
        spend totals.
      </p>
    </CoreShell>
  );
}
