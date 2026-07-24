"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type EditOrganisation, type EditPlan, type EditSummary } from "@/lib/api";
import { PageHeader } from "@/components/PageHeader";
import { SiteHeader } from "@/components/SiteHeader";

export default function EditAdminHomePage() {
  const [summary, setSummary] = useState<EditSummary | null>(null);
  const [orgs, setOrgs] = useState<EditOrganisation[]>([]);
  const [plans, setPlans] = useState<EditPlan[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void Promise.all([api.editSummary(), api.editListOrganisations(), api.editListPlans()])
      .then(([s, o, p]) => {
        setSummary(s);
        setOrgs(o);
        setPlans(p);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed"));
  }, []);

  return (
    <main className="min-h-screen pb-20">
      <SiteHeader />
      <div className="ac-container pt-10 md:pt-14">
        <PageHeader
          eyebrow="Art City Edit · Admin"
          title="Operations console"
          description="Approval queue, customer accounts, plan configuration, and feature flags."
          actions={
            <Link href="/edit/admin/applications" className="ac-btn ac-btn-primary">
              Approval queue
            </Link>
          }
        />

        {error ? <p className="mb-4 text-[var(--danger)]">{error}</p> : null}

        {summary ? (
          <div className="mb-10 grid gap-4 md:grid-cols-3">
            <div className="border border-[var(--line)] p-5">
              <p className="ac-display text-[var(--gold-bright)]">Pending applications</p>
              <p className="mt-2 text-3xl text-[var(--paper)]">{summary.pending_applications}</p>
            </div>
            <div className="border border-[var(--line)] p-5">
              <p className="ac-display text-[var(--gold-bright)]">Workspaces</p>
              <p className="mt-2 text-3xl text-[var(--paper)]">{summary.workspaces}</p>
            </div>
            <div className="border border-[var(--line)] p-5">
              <p className="ac-display text-[var(--gold-bright)]">Feature flags</p>
              <p className="mt-2 text-sm text-[var(--mist)]">
                {Object.entries(summary.feature_flags)
                  .map(([k, v]) => `${k}: ${v ? "on" : "off"}`)
                  .join(" · ")}
              </p>
            </div>
          </div>
        ) : null}

        <section className="mb-12">
          <h2 className="ac-display mb-4 text-xl">Plans</h2>
          <ul className="border-t border-[var(--line)]">
            {plans.map((p) => (
              <li key={p.id} className="py-4 text-sm text-[var(--mist)]">
                <span className="ac-display text-[var(--paper)]">{p.name}</span>
                <span className="ml-3">{p.code}</span>
                {p.price_usd_monthly != null ? (
                  <span className="ml-3">${p.price_usd_monthly}/mo</span>
                ) : null}
              </li>
            ))}
          </ul>
        </section>

        <section>
          <h2 className="ac-display mb-4 text-xl">Organisations</h2>
          <ul className="border-t border-[var(--line)]">
            {orgs.map((o) => (
              <li key={o.id} className="flex flex-wrap items-center justify-between gap-3 py-4">
                <div>
                  <p className="ac-display text-[var(--paper)]">{o.display_name}</p>
                  <p className="text-[0.72rem] tracking-[0.14em] text-[var(--mist-soft)] uppercase">
                    {o.status.replaceAll("_", " ")} · {o.org_type}
                  </p>
                </div>
                {o.status === "approved_pending_billing" ? (
                  <button
                    type="button"
                    className="ac-btn"
                    onClick={() =>
                      void api
                        .editActivateSubscription(o.id, "creator")
                        .then(() => api.editListOrganisations().then(setOrgs))
                        .catch((e) => setError(e instanceof Error ? e.message : "Activate failed"))
                    }
                  >
                    Activate invoice
                  </button>
                ) : null}
              </li>
            ))}
          </ul>
        </section>
      </div>
    </main>
  );
}
