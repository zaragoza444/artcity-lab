"use client";

import { FormEvent, useEffect, useState } from "react";
import { CoreShell } from "@/components/CoreShell";
import { api, type KnowledgeEntry } from "@/lib/api";

export default function KnowledgePage() {
  const [q, setQ] = useState("");
  const [entries, setEntries] = useState<KnowledgeEntry[]>([]);

  function load(term?: string) {
    api.listKnowledge(term).then(setEntries).catch(() => undefined);
  }

  useEffect(() => {
    load();
  }, []);

  function onSearch(e: FormEvent) {
    e.preventDefault();
    load(q);
  }

  return (
    <CoreShell
      title="Kurdish Knowledge Base"
      subtitle="Terminology, geography, customs, and Story Bible entries for Cinema and Studio prompt consistency."
    >
      <form onSubmit={onSearch} className="mb-6 flex gap-2">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search terms"
          className="flex-1 border border-[var(--line)] bg-[var(--ink-soft)] px-3 py-2 text-[var(--paper)]"
        />
        <button
          type="submit"
          className="border border-[var(--gold)] px-4 py-2 text-xs uppercase tracking-[0.14em] text-[var(--gold-bright)]"
        >
          Search
        </button>
      </form>
      <ul className="space-y-3">
        {entries.map((e) => (
          <li key={e.id} className="border border-[var(--line)] px-4 py-4">
            <p className="text-[var(--paper)]">
              {e.term}{" "}
              <span className="text-xs text-[var(--mist)]">
                {e.dialect || e.language} · {e.approval_status}
              </span>
            </p>
            <p className="mt-1 text-sm text-[var(--mist)]">{e.definition}</p>
          </li>
        ))}
      </ul>
    </CoreShell>
  );
}
