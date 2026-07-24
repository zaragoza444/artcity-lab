"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type EditAccessApplication } from "@/lib/api";
import { PageHeader } from "@/components/PageHeader";
import { SiteHeader } from "@/components/SiteHeader";

export default function EditAdminApplicationsPage() {
  const [rows, setRows] = useState<EditAccessApplication[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const load = async () => {
    try {
      setRows(await api.editListApplications());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Admin access required");
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const review = async (id: string, action: string) => {
    setBusy(id);
    setError(null);
    try {
      await api.editReviewApplication(id, {
        action,
        reason: action === "reject" ? "Does not meet Art City criteria" : undefined,
        plan_code: action === "approve" ? undefined : undefined,
      });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Review failed");
    } finally {
      setBusy(null);
    }
  };

  return (
    <main className="min-h-screen pb-20">
      <SiteHeader />
      <div className="ac-container pt-10 md:pt-14">
        <PageHeader
          eyebrow="Art City Edit · Admin"
          title="Access approval queue"
          description="Approve, reject, or request more information. Approval alone does not activate processing until billing/entitlements are complete (internal plans activate immediately)."
          actions={
            <Link href="/edit" className="ac-btn">
              Edit hub
            </Link>
          }
        />

        {error ? <p className="mb-4 text-[var(--danger)]">{error}</p> : null}

        <ul className="border-t border-[var(--line)]">
          {rows.map((a) => (
            <li key={a.id} className="border-b border-[var(--line)] py-6">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <p className="ac-display text-xl text-[var(--paper)]">{a.organisation_name}</p>
                  <p className="mt-2 text-[0.72rem] tracking-[0.14em] text-[var(--mist-soft)] uppercase">
                    {a.state.replaceAll("_", " ")} · plan {a.requested_plan_code}
                  </p>
                  {a.use_case ? (
                    <p className="mt-2 max-w-xl text-sm text-[var(--mist)]">{a.use_case}</p>
                  ) : null}
                </div>
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    className="ac-btn ac-btn-primary"
                    disabled={busy === a.id}
                    onClick={() => void review(a.id, "approve")}
                  >
                    Approve
                  </button>
                  <button
                    type="button"
                    className="ac-btn"
                    disabled={busy === a.id}
                    onClick={() => void review(a.id, "request_info")}
                  >
                    Request info
                  </button>
                  <button
                    type="button"
                    className="ac-btn"
                    disabled={busy === a.id}
                    onClick={() => void review(a.id, "reject")}
                  >
                    Reject
                  </button>
                  <button
                    type="button"
                    className="ac-btn"
                    disabled={busy === a.id}
                    onClick={() => void review(a.id, "suspend")}
                  >
                    Suspend
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>
        {rows.length === 0 && !error ? (
          <p className="mt-8 text-sm text-[var(--mist)]">No applications in queue.</p>
        ) : null}
      </div>
    </main>
  );
}
