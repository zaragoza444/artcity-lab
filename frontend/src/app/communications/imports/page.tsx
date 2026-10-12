"use client";

import { useState } from "react";
import { CommError, CommunicationsFrame } from "@/components/CommunicationsFrame";
import { useLocale } from "@/components/LocaleProvider";
import { commRequest } from "@/lib/communications";

type Job = {
  job_id: string;
  total: number;
  inserted: number;
  updated: number;
  rejected: number;
  rejections: Record<string, number>;
  with_valid_marketing_opt_in: number;
  requires_consent: number;
};

export default function ImportsPage() {
  const { t } = useLocale();
  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState("");

  return (
    <CommunicationsFrame title={t("comm.imports")}>
      <CommError error={error} />
      <form
        className="space-y-3"
        onSubmit={async (event) => {
          event.preventDefault();
          const input = (event.currentTarget.elements.namedItem("file") as HTMLInputElement).files?.[0];
          if (!input) return;
          const body = new FormData();
          body.append("file", input);
          try {
            const created = await commRequest<Job>("/contacts/imports", { method: "POST", body });
            setJob(created);
          } catch (err) {
            setError(err instanceof Error ? err.message : "Import failed");
          }
        }}
      >
        <input name="file" type="file" accept=".csv,.xlsx" className="block text-sm" />
        <button className="ac-btn ac-btn-primary" type="submit">Import</button>
      </form>
      {job ? (
        <dl className="mt-6 grid gap-2 text-sm sm:grid-cols-2">
          <div>Total {job.total}</div>
          <div>Inserted {job.inserted}</div>
          <div>Updated {job.updated}</div>
          <div>Rejected {job.rejected}</div>
          <div>Proven marketing opt-in {job.with_valid_marketing_opt_in}</div>
          <div>Needs consent {job.requires_consent}</div>
          <div className="sm:col-span-2">Rejections {JSON.stringify(job.rejections)}</div>
        </dl>
      ) : null}
    </CommunicationsFrame>
  );
}
