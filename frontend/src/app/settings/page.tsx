"use client";

import { CoreShell } from "@/components/CoreShell";

export default function SettingsPage() {
  return (
    <CoreShell
      title="Settings"
      subtitle="Environment, external provider fallback, and Art City-controlled inference flags."
    >
      <ul className="space-y-2 text-sm text-[var(--mist)]">
        <li>EXTERNAL_PROVIDERS_ENABLED — disable third-party fallback without breaking Gateway</li>
        <li>AUTH_REQUIRED — JWT on all mutate APIs</li>
        <li>Separate staging / production env vars on Railway</li>
        <li>Never commit .env, datasets, or model weights</li>
      </ul>
    </CoreShell>
  );
}
