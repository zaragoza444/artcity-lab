"use client";

import { useEffect, useState } from "react";
import { CommError, CommunicationsFrame } from "@/components/CommunicationsFrame";
import { useLocale } from "@/components/LocaleProvider";
import { commRequest } from "@/lib/communications";

type Overview = {
  senders: number;
  contacts: number;
  accepted_today: number;
  delivered_today: number;
  failed_today: number;
  replied_today: number;
  provisional_usd: string;
  live_send_enabled: boolean;
  business_units: { id: string; name: string }[];
};

export default function CommunicationsHomePage() {
  const { t } = useLocale();
  const [data, setData] = useState<Overview | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    commRequest<Overview>("/overview")
      .then(setData)
      .catch((err: Error) => setError(err.message));
  }, []);

  return (
    <CommunicationsFrame title={t("comm.overview")}>
      <CommError error={error} />
      {data ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            ["Senders", data.senders],
            ["Contacts", data.contacts],
            ["Accepted today", data.accepted_today],
            ["Delivered today", data.delivered_today],
            ["Failed today", data.failed_today],
            ["Replies today", data.replied_today],
            ["Provisional USD", data.provisional_usd],
            ["Live send", data.live_send_enabled ? "on" : "off"],
          ].map(([label, value]) => (
            <div key={String(label)} className="border border-[var(--line)] p-4">
              <p className="text-[0.68rem] uppercase tracking-[0.14em] text-[var(--mist)]">{label}</p>
              <p className="mt-2 text-2xl text-[var(--paper)]">{value}</p>
            </div>
          ))}
        </div>
      ) : null}
    </CommunicationsFrame>
  );
}
