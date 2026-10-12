"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { CommError, CommunicationsFrame } from "@/components/CommunicationsFrame";
import { commRequest } from "@/lib/communications";

type Detail = {
  id: string;
  name: string;
  state: string;
  pause_reason: string | null;
  quote_usd: string;
  reserved_usd: string;
  consumed_usd: string;
  stats: {
    selected: number;
    eligible: number;
    api_accepted: number;
    delivered: number;
    read: number;
    read_receipts: string;
    failed: number;
    excluded: Record<string, number>;
    delivery_rate: number | null;
  };
};

export default function CampaignDetailPage() {
  const params = useParams<{ id: string }>();
  const [row, setRow] = useState<Detail | null>(null);
  const [error, setError] = useState("");
  const [messageId, setMessageId] = useState("");

  async function load() {
    setRow(await commRequest<Detail>(`/campaigns/${params.id}`));
  }

  useEffect(() => {
    load().catch((err: Error) => setError(err.message));
  }, [params.id]);

  return (
    <CommunicationsFrame title={row?.name || "Campaign"}>
      <CommError error={error} />
      {row ? (
        <div className="space-y-4 text-sm">
          <p>State {row.state} {row.pause_reason ? `· ${row.pause_reason}` : ""}</p>
          <p>Quote {row.quote_usd} · Reserved {row.reserved_usd} · Consumed {row.consumed_usd}</p>
          <p>
            Selected {row.stats.selected} · Eligible {row.stats.eligible} · Accepted {row.stats.api_accepted} · Delivered {row.stats.delivered} · Read {row.stats.read} ({row.stats.read_receipts}) · Failed {row.stats.failed}
          </p>
          <p>Exclusions {JSON.stringify(row.stats.excluded)}</p>
          <div className="flex flex-wrap gap-2">
            <button className="ac-btn" type="button" onClick={() => commRequest(`/campaigns/${row.id}/pause`, { method: "POST" }).then(load).catch((err: Error) => setError(err.message))}>Pause</button>
            <button className="ac-btn" type="button" onClick={() => commRequest(`/campaigns/${row.id}/resume`, { method: "POST" }).then(load).catch((err: Error) => setError(err.message))}>Resume</button>
            <button className="ac-btn" type="button" onClick={() => commRequest(`/campaigns/${row.id}/tick`, { method: "POST" }).then(load).catch((err: Error) => setError(err.message))}>Dispatch queued</button>
          </div>
          <form
            className="flex flex-wrap gap-2"
            onSubmit={async (event) => {
              event.preventDefault();
              try {
                await commRequest("/administration/simulate-delivery", {
                  method: "POST",
                  body: JSON.stringify({ provider_message_id: messageId, status: "delivered" }),
                });
                await load();
              } catch (err) {
                setError(err instanceof Error ? err.message : "Could not simulate delivery");
              }
            }}
          >
            <input className="ac-input" placeholder="Provider message id" value={messageId} onChange={(e) => setMessageId(e.target.value)} dir="ltr" />
            <button className="ac-btn" type="submit">Simulate delivery</button>
          </form>
        </div>
      ) : null}
    </CommunicationsFrame>
  );
}
