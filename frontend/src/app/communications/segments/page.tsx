"use client";

import { useEffect, useState } from "react";
import { CommError, CommunicationsFrame } from "@/components/CommunicationsFrame";
import { useLocale } from "@/components/LocaleProvider";
import { commRequest } from "@/lib/communications";

type Segment = { id: string; name: string; filter_json: Record<string, unknown> };

export default function SegmentsPage() {
  const { t } = useLocale();
  const [rows, setRows] = useState<Segment[]>([]);
  const [name, setName] = useState("");
  const [city, setCity] = useState("");
  const [error, setError] = useState("");

  async function load() {
    setRows(await commRequest<Segment[]>("/segments"));
  }

  useEffect(() => {
    load().catch((err: Error) => setError(err.message));
  }, []);

  return (
    <CommunicationsFrame title={t("comm.segments")}>
      <CommError error={error} />
      <form
        className="mb-6 flex flex-wrap gap-2"
        onSubmit={async (event) => {
          event.preventDefault();
          try {
            await commRequest("/segments", {
              method: "POST",
              body: JSON.stringify({ name, filter_json: city ? { city } : {} }),
            });
            setName("");
            setCity("");
            await load();
          } catch (err) {
            setError(err instanceof Error ? err.message : "Could not save segment");
          }
        }}
      >
        <input className="ac-input" placeholder="Segment name" value={name} onChange={(e) => setName(e.target.value)} />
        <input className="ac-input" placeholder="City filter" value={city} onChange={(e) => setCity(e.target.value)} dir="auto" />
        <button className="ac-btn ac-btn-primary" type="submit">Save</button>
      </form>
      <ul className="space-y-2">
        {rows.map((row) => (
          <li key={row.id} className="border border-[var(--line)] px-3 py-2 text-sm">
            {row.name} · {JSON.stringify(row.filter_json)}
          </li>
        ))}
      </ul>
    </CommunicationsFrame>
  );
}
