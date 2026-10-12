"use client";

import { useEffect, useState } from "react";
import { CommError, CommunicationsFrame } from "@/components/CommunicationsFrame";
import { useLocale } from "@/components/LocaleProvider";
import { commRequest } from "@/lib/communications";

type Contact = { id: string; phone: string; display_name: string | null; city: string | null; country_iso: string | null; preferred_locale: string | null };

export default function ContactsPage() {
  const { t } = useLocale();
  const [rows, setRows] = useState<Contact[]>([]);
  const [error, setError] = useState("");
  const [phone, setPhone] = useState("");
  const [name, setName] = useState("");
  const [query, setQuery] = useState("");

  async function load(q = query) {
    const data = await commRequest<Contact[]>(`/contacts${q ? `?q=${encodeURIComponent(q)}` : ""}`);
    setRows(data);
  }

  useEffect(() => {
    load("").catch((err: Error) => setError(err.message));
  }, []);

  return (
    <CommunicationsFrame title={t("comm.contacts")}>
      <CommError error={error} />
      <form
        className="mb-6 flex flex-wrap gap-2"
        onSubmit={async (event) => {
          event.preventDefault();
          try {
            await commRequest("/contacts", { method: "POST", body: JSON.stringify({ phone_number: phone, display_name: name }) });
            setPhone("");
            setName("");
            await load();
          } catch (err) {
            setError(err instanceof Error ? err.message : "Could not add contact");
          }
        }}
      >
        <input className="ac-input" placeholder="Phone" value={phone} onChange={(e) => setPhone(e.target.value)} dir="ltr" />
        <input className="ac-input" placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} dir="auto" />
        <button className="ac-btn ac-btn-primary" type="submit">Add</button>
        <input className="ac-input" placeholder="Search" value={query} onChange={(e) => setQuery(e.target.value)} />
        <button className="ac-btn" type="button" onClick={() => load().catch((err: Error) => setError(err.message))}>Search</button>
      </form>
      <p className="mb-4 text-sm text-[var(--mist)]">Adding a contact does not record marketing consent.</p>
      <ul className="space-y-2">
        {rows.map((row) => (
          <li key={row.id} className="border border-[var(--line)] px-3 py-2 text-sm">
            <span dir="ltr">{row.phone}</span> · <span dir="auto">{row.display_name}</span> · {row.city} · {row.country_iso} · {row.preferred_locale}
          </li>
        ))}
      </ul>
    </CommunicationsFrame>
  );
}
