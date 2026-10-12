"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { CommError, CommunicationsFrame } from "@/components/CommunicationsFrame";
import { useLocale } from "@/components/LocaleProvider";
import { commRequest } from "@/lib/communications";

type Sender = { id: string; display_name: string | null; phone_masked: string };
type Template = { id: string; meta_name: string; language_code: string; status: string; category: string };
type Segment = { id: string; name: string };
type Campaign = { id: string; name: string; state: string; quote_usd: string; budget_usd: string };
type Preview = {
  selected: number;
  eligible: number;
  excluded: Record<string, number>;
  quote_usd: string;
  samples: { parameters: Record<string, string[]> }[];
  blocking_errors: string[];
  can_submit: boolean;
  budget_feasible: boolean;
};

export default function CampaignsPage() {
  const { t } = useLocale();
  const [senders, setSenders] = useState<Sender[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [segments, setSegments] = useState<Segment[]>([]);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [senderId, setSenderId] = useState("");
  const [templateId, setTemplateId] = useState("");
  const [segmentId, setSegmentId] = useState("");
  const [name, setName] = useState("Art City seminar");
  const [budget, setBudget] = useState("20.00");
  const [variable, setVariable] = useState("{{name}}");
  const [phone, setPhone] = useState("");
  const [display, setDisplay] = useState("Art City");
  const [preview, setPreview] = useState<Preview | null>(null);
  const [currentId, setCurrentId] = useState("");
  const [error, setError] = useState("");

  async function load() {
    const [senderRows, templateRows, segmentRows, campaignRows] = await Promise.all([
      commRequest<Sender[]>("/senders"),
      commRequest<Template[]>("/templates"),
      commRequest<Segment[]>("/segments"),
      commRequest<Campaign[]>("/campaigns"),
    ]);
    setSenders(senderRows);
    setTemplates(templateRows);
    setSegments(segmentRows);
    setCampaigns(campaignRows);
    if (!senderId && senderRows[0]) setSenderId(senderRows[0].id);
    if (!templateId && templateRows[0]) setTemplateId(templateRows[0].id);
  }

  useEffect(() => {
    load().catch((err: Error) => setError(err.message));
  }, []);

  return (
    <CommunicationsFrame title={t("comm.campaigns")}>
      <CommError error={error} />
      <form
        className="mb-8 grid gap-3 md:grid-cols-2"
        onSubmit={async (event) => {
          event.preventDefault();
          try {
            let sender = senderId;
            if (!sender) {
              const created = await commRequest<Sender>("/senders", {
                method: "POST",
                body: JSON.stringify({ phone_e164: phone, display_name: display, unique_recipient_limit: 1000 }),
              });
              sender = created.id;
              setSenderId(sender);
            }
            const campaign = await commRequest<Campaign>("/campaigns", {
              method: "POST",
              body: JSON.stringify({
                name,
                sender_id: sender,
                template_id: templateId,
                segment_id: segmentId || null,
                maximum_budget_usd: budget,
                parameter_template: { body: [variable], header: [], buttons: [] },
                quiet_hours: { start: "21:00", end: "09:00" },
              }),
            });
            setCurrentId(campaign.id);
            const report = await commRequest<Preview>(`/campaigns/${campaign.id}/preview`, { method: "POST" });
            setPreview(report);
            await load();
          } catch (err) {
            setError(err instanceof Error ? err.message : "Could not create campaign");
          }
        }}
      >
        <input className="ac-input" value={name} onChange={(e) => setName(e.target.value)} />
        <input className="ac-input" value={budget} onChange={(e) => setBudget(e.target.value)} dir="ltr" />
        <input className="ac-input" placeholder="Sender phone if none exists" value={phone} onChange={(e) => setPhone(e.target.value)} dir="ltr" />
        <input className="ac-input" value={display} onChange={(e) => setDisplay(e.target.value)} />
        <select className="ac-input" value={senderId} onChange={(e) => setSenderId(e.target.value)}>
          <option value="">New sender from the phone field</option>
          {senders.map((row) => (
            <option key={row.id} value={row.id}>{row.display_name} {row.phone_masked}</option>
          ))}
        </select>
        <select className="ac-input" value={templateId} onChange={(e) => setTemplateId(e.target.value)}>
          <option value="">Choose an approved template</option>
          {templates.filter((row) => row.status === "approved").map((row) => (
            <option key={row.id} value={row.id}>{row.meta_name} ({row.language_code})</option>
          ))}
        </select>
        <select className="ac-input" value={segmentId} onChange={(e) => setSegmentId(e.target.value)}>
          <option value="">All contacts</option>
          {segments.map((row) => (
            <option key={row.id} value={row.id}>{row.name}</option>
          ))}
        </select>
        <input className="ac-input" value={variable} onChange={(e) => setVariable(e.target.value)} dir="ltr" />
        <button className="ac-btn ac-btn-primary" type="submit">Preview campaign</button>
      </form>
      {preview ? (
        <section className="mb-8 border border-[var(--line)] p-4 text-sm">
          <p>Selected {preview.selected} · Eligible {preview.eligible} · Quote USD {preview.quote_usd}</p>
          <p>Excluded {JSON.stringify(preview.excluded)}</p>
          <p>Budget covers quote: {preview.budget_feasible ? "yes" : "no"} · Can submit: {preview.can_submit ? "yes" : "no"}</p>
          <p>Blocking {preview.blocking_errors.join(", ") || "none"}</p>
          <ul className="mt-2 space-y-1">
            {preview.samples.map((sample, index) => (
              <li key={index} dir="auto">Sample {index + 1}: {JSON.stringify(sample.parameters)}</li>
            ))}
          </ul>
          <div className="mt-3 flex flex-wrap gap-2">
            <button className="ac-btn" type="button" onClick={() => commRequest(`/campaigns/${currentId}/submit`, { method: "POST" }).then(load).catch((err: Error) => setError(err.message))}>Submit</button>
            <button className="ac-btn" type="button" onClick={() => commRequest(`/campaigns/${currentId}/approve`, { method: "POST" }).then(load).catch((err: Error) => setError(err.message))}>Approve</button>
            <button className="ac-btn" type="button" onClick={() => commRequest(`/campaigns/${currentId}/schedule`, { method: "POST" }).then(load).catch((err: Error) => setError(err.message))}>Schedule</button>
          </div>
        </section>
      ) : null}
      <ul className="space-y-2">
        {campaigns.map((row) => (
          <li key={row.id} className="border border-[var(--line)] px-3 py-2 text-sm">
            <Link href={`/communications/campaigns/${row.id}`}>{row.name}</Link> · {row.state} · quote {row.quote_usd} · budget {row.budget_usd}
          </li>
        ))}
      </ul>
    </CommunicationsFrame>
  );
}
