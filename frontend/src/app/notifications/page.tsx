"use client";

import { CoreShell } from "@/components/CoreShell";

export default function NotificationsPage() {
  return (
    <CoreShell
      title="Notifications"
      subtitle="Job completion, rights review, and training approval alerts (shell for Sprint 2+)."
    >
      <p className="text-[var(--mist)]">No pending notifications.</p>
    </CoreShell>
  );
}
