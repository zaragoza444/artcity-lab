"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type EditAccessApplication, type EditPlan } from "@/lib/api";
import { PageHeader } from "@/components/PageHeader";
import { SiteHeader } from "@/components/SiteHeader";

export default function EditApplyPage() {
  const [plans, setPlans] = useState<EditPlan[]>([]);
  const [mine, setMine] = useState<EditAccessApplication[]>([]);
  const [organisationName, setOrganisationName] = useState("");
  const [planCode, setPlanCode] = useState("creator");
  const [useCase, setUseCase] = useState("");
  const [country, setCountry] = useState("");
  const [website, setWebsite] = useState("");
  const [minutes, setMinutes] = useState(120);
  const [accepted, setAccepted] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);

  useEffect(() => {
    void Promise.all([api.editListPlans(), api.editMyApplications()])
      .then(([p, m]) => {
        setPlans(p.filter((x) => x.code !== "internal_art_city"));
        setMine(m);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed"));
  }, []);

  const submit = async () => {
    setBusy(true);
    setError(null);
    setOk(null);
    try {
      const app = await api.editSubmitApplication({
        organisation_name: organisationName,
        requested_plan_code: planCode,
        use_case: useCase,
        expected_monthly_minutes: minutes,
        country,
        website,
        declarations_accepted: accepted,
      });
      setOk(`Application submitted (${app.state}). Art City will review before activation.`);
      setMine(await api.editMyApplications());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Submit failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="min-h-screen pb-20">
      <SiteHeader />
      <div className="ac-container pt-10 md:pt-14">
        <PageHeader
          eyebrow="Art City Edit"
          title="Request access"
          description="Registration creates an identity, not a production account. Art City must approve your organisation and activate entitlements before media processing."
          actions={
            <Link href="/edit" className="ac-btn">
              Back to Edit
            </Link>
          }
        />

        {error ? <p className="mb-4 text-[var(--danger)]">{error}</p> : null}
        {ok ? <p className="mb-4 text-[var(--mist)]">{ok}</p> : null}

        <form
          className="max-w-xl space-y-4 border border-[var(--line)] p-6"
          onSubmit={(e) => {
            e.preventDefault();
            void submit();
          }}
        >
          <input
            className="ac-input w-full"
            required
            placeholder="Organisation name"
            value={organisationName}
            onChange={(e) => setOrganisationName(e.target.value)}
          />
          <select
            className="ac-input w-full"
            value={planCode}
            onChange={(e) => setPlanCode(e.target.value)}
          >
            {plans.map((p) => (
              <option key={p.id} value={p.code}>
                {p.name}
                {p.price_usd_monthly != null ? ` · $${p.price_usd_monthly}/mo` : " · enterprise"}
              </option>
            ))}
          </select>
          <textarea
            className="ac-input w-full min-h-[100px]"
            placeholder="Intended use case"
            value={useCase}
            onChange={(e) => setUseCase(e.target.value)}
          />
          <input
            className="ac-input w-full"
            placeholder="Country"
            value={country}
            onChange={(e) => setCountry(e.target.value)}
          />
          <input
            className="ac-input w-full"
            placeholder="Website"
            value={website}
            onChange={(e) => setWebsite(e.target.value)}
          />
          <label className="block text-sm text-[var(--mist)]">
            Expected monthly minutes
            <input
              type="number"
              className="ac-input mt-1 w-full"
              value={minutes}
              onChange={(e) => setMinutes(Number(e.target.value))}
            />
          </label>
          <label className="flex items-start gap-3 text-sm text-[var(--mist)]">
            <input
              type="checkbox"
              checked={accepted}
              onChange={(e) => setAccepted(e.target.checked)}
              className="mt-1"
              required
            />
            I accept Terms, Privacy, Acceptable Use, and rights warranty declarations.
          </label>
          <button type="submit" className="ac-btn ac-btn-primary" disabled={busy || !accepted}>
            {busy ? "Submitting…" : "Submit for Art City review"}
          </button>
        </form>

        {mine.length > 0 ? (
          <section className="mt-12">
            <h2 className="ac-display mb-4 text-xl">Your applications</h2>
            <ul className="border-t border-[var(--line)]">
              {mine.map((a) => (
                <li key={a.id} className="py-4 text-sm text-[var(--mist)]">
                  <span className="ac-display text-[var(--paper)]">{a.organisation_name}</span>
                  <span className="ml-3 uppercase tracking-[0.14em]">{a.state.replaceAll("_", " ")}</span>
                  {a.decision_reason ? <p className="mt-1">{a.decision_reason}</p> : null}
                </li>
              ))}
            </ul>
          </section>
        ) : null}
      </div>
    </main>
  );
}
