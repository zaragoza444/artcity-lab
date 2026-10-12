"use client";

import { useEffect, useState } from "react";
import { CommError, CommunicationsFrame } from "@/components/CommunicationsFrame";
import { useLocale } from "@/components/LocaleProvider";
import { commRequest } from "@/lib/communications";

type Template = { id: string; meta_name: string; language_code: string; category: string; status: string };

export default function TemplatesPage() {
  const { t } = useLocale();
  const [rows, setRows] = useState<Template[]>([]);
  const [name, setName] = useState("art_city_event_invite_en");
  const [language, setLanguage] = useState("en_US");
  const [error, setError] = useState("");

  async function load() {
    setRows(await commRequest<Template[]>("/templates"));
  }

  useEffect(() => {
    load().catch((err: Error) => setError(err.message));
  }, []);

  return (
    <CommunicationsFrame title={t("comm.templates")}>
      <CommError error={error} />
      <p className="mb-4 text-sm text-[var(--mist)]">Language codes come from Meta. An English or Arabic template is not labeled Kurdish.</p>
      <form
        className="mb-6 flex flex-wrap gap-2"
        onSubmit={async (event) => {
          event.preventDefault();
          try {
            await commRequest("/templates", {
              method: "POST",
              body: JSON.stringify({ meta_name: name, language_code: language, category: "marketing", body_param_count: 1 }),
            });
            await load();
          } catch (err) {
            setError(err instanceof Error ? err.message : "Could not register template");
          }
        }}
      >
        <input className="ac-input" value={name} onChange={(e) => setName(e.target.value)} dir="ltr" />
        <input className="ac-input" value={language} onChange={(e) => setLanguage(e.target.value)} dir="ltr" />
        <button className="ac-btn ac-btn-primary" type="submit">Register local template</button>
      </form>
      <ul className="space-y-2">
        {rows.map((row) => (
          <li key={row.id} className="border border-[var(--line)] px-3 py-2 text-sm" dir="ltr">
            {row.meta_name} · {row.language_code} · {row.category} · {row.status}
          </li>
        ))}
      </ul>
    </CommunicationsFrame>
  );
}
