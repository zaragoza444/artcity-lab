"use client";

import { useEffect, useState } from "react";
import { CommError, CommunicationsFrame } from "@/components/CommunicationsFrame";
import { useLocale } from "@/components/LocaleProvider";
import { commRequest } from "@/lib/communications";

type Rate = { id: string; market: string; category: string; unit_rate: string; valid_from: string; valid_to: string | null; source: string };
type Summary = { provisional_usd: string; adjustments_usd: string; reconciled_usd: string; daily_cap_usd: string };

export default function BillingPage() {
  const { t } = useLocale();
  const [rates, setRates] = useState<Rate[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [invoice, setInvoice] = useState("");
  const [amount, setAmount] = useState("");
  const [error, setError] = useState("");

  async function load() {
    const [rateRows, summaryRow] = await Promise.all([
      commRequest<Rate[]>("/billing/rates"),
      commRequest<Summary>("/billing/summary"),
    ]);
    setRates(rateRows);
    setSummary(summaryRow);
  }

  useEffect(() => {
    load().catch((err: Error) => setError(err.message));
  }, []);

  return (
    <CommunicationsFrame title={t("comm.billing")}>
      <CommError error={error} />
      {summary ? (
        <p className="mb-4 text-sm">
          Provisional {summary.provisional_usd} · Adjustments {summary.adjustments_usd} · Reconciled {summary.reconciled_usd} · Daily cap {summary.daily_cap_usd}
        </p>
      ) : null}
      <ul className="mb-6 space-y-2 text-sm">
        {rates.map((row) => (
          <li key={row.id} className="border border-[var(--line)] px-3 py-2" dir="ltr">
            {row.market} {row.category} {row.unit_rate} USD · from {row.valid_from} {row.valid_to ? `to ${row.valid_to}` : ""} · {row.source}
          </li>
        ))}
      </ul>
      <form
        className="flex flex-wrap gap-2"
        onSubmit={async (event) => {
          event.preventDefault();
          try {
            await commRequest("/billing/reconcile", {
              method: "POST",
              body: JSON.stringify({ external_invoice_ref: invoice, amount_usd: amount }),
            });
            await load();
          } catch (err) {
            setError(err instanceof Error ? err.message : "Reconciliation failed");
          }
        }}
      >
        <input className="ac-input" placeholder="Invoice ref" value={invoice} onChange={(e) => setInvoice(e.target.value)} />
        <input className="ac-input" placeholder="Invoice USD" value={amount} onChange={(e) => setAmount(e.target.value)} dir="ltr" />
        <button className="ac-btn ac-btn-primary" type="submit">Reconcile</button>
      </form>
    </CommunicationsFrame>
  );
}
