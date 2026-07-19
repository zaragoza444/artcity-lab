"use client";

import { CoreShell } from "@/components/CoreShell";

export default function AnnotationsPage() {
  return (
    <CoreShell
      title="Annotations"
      subtitle="Reviewer workspace for text, speech, image, video, and music labels with approval, conflict resolution, and export."
    >
      <p className="max-w-2xl text-[var(--mist)]">
        Create tasks via <code className="text-[var(--paper-dim)]">POST /api/data-lab/annotations</code>.
        Labels, comments, and revision history are stored per task for training-manifest export.
      </p>
    </CoreShell>
  );
}
