"use client";

import { FormEvent, useEffect, useState } from "react";
import { CoreShell } from "@/components/CoreShell";
import { api, type KnowledgeEntry } from "@/lib/api";

const DIALECTS = [
  { id: "", label: "All dialects" },
  { id: "sorani", label: "Sorani" },
  { id: "badini", label: "Badini" },
  { id: "kurmanji", label: "Kurmanji" },
];

export default function KnowledgePage() {
  const [q, setQ] = useState("");
  const [dialect, setDialect] = useState("");
  const [entries, setEntries] = useState<KnowledgeEntry[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [term, setTerm] = useState("");
  const [definition, setDefinition] = useState("");
  const [translation, setTranslation] = useState("");
  const [entryDialect, setEntryDialect] = useState("sorani");
  const [category, setCategory] = useState("terminology");

  function load(termQ?: string, d?: string) {
    api
      .listKnowledge(termQ, d || undefined)
      .then(setEntries)
      .catch(() => undefined);
  }

  useEffect(() => {
    load();
  }, []);

  function onSearch(e: FormEvent) {
    e.preventDefault();
    load(q, dialect);
  }

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    if (!term.trim() || !definition.trim()) return;
    setBusy(true);
    setError(null);
    try {
      await api.createKnowledge({
        term: term.trim(),
        definition: definition.trim(),
        translation: translation.trim() || undefined,
        dialect: entryDialect,
        category,
        language: "ku",
      });
      setTerm("");
      setDefinition("");
      setTranslation("");
      load(q, dialect);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Create failed");
    } finally {
      setBusy(false);
    }
  }

  async function onApprove(id: string) {
    setBusy(true);
    try {
      await api.approveKnowledge(id);
      load(q, dialect);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Approve failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <CoreShell
      title="Kurdish Knowledge Base"
      subtitle="Sorani, Badini, and Kurmanji terminology for Cinema and Studio cultural consistency."
    >
      <form onSubmit={onSearch} className="mb-8 flex flex-wrap gap-2">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search terms"
          className="min-w-[12rem] flex-1 border border-[var(--line)] bg-[var(--ink-soft)] px-3 py-2 text-[var(--paper)]"
        />
        <select
          value={dialect}
          onChange={(e) => setDialect(e.target.value)}
          className="border border-[var(--line)] bg-[var(--ink-soft)] px-3 py-2 text-[var(--paper)]"
        >
          {DIALECTS.map((d) => (
            <option key={d.id || "all"} value={d.id}>
              {d.label}
            </option>
          ))}
        </select>
        <button
          type="submit"
          className="border border-[var(--gold)] px-4 py-2 text-xs uppercase tracking-[0.14em] text-[var(--gold-bright)]"
        >
          Search
        </button>
      </form>

      <form onSubmit={onCreate} className="mb-10 grid gap-3 border border-[var(--line)] p-5 md:grid-cols-2">
        <p className="md:col-span-2 text-[0.7rem] uppercase tracking-[0.14em] text-[var(--mist)]">
          Add knowledge entry
        </p>
        <input
          value={term}
          onChange={(e) => setTerm(e.target.value)}
          placeholder="Term"
          className="border border-[var(--line)] bg-[var(--ink-soft)] px-3 py-2 text-[var(--paper)]"
          required
        />
        <select
          value={entryDialect}
          onChange={(e) => setEntryDialect(e.target.value)}
          className="border border-[var(--line)] bg-[var(--ink-soft)] px-3 py-2 text-[var(--paper)]"
        >
          <option value="sorani">Sorani</option>
          <option value="badini">Badini</option>
          <option value="kurmanji">Kurmanji</option>
        </select>
        <textarea
          value={definition}
          onChange={(e) => setDefinition(e.target.value)}
          placeholder="Definition"
          rows={3}
          className="md:col-span-2 border border-[var(--line)] bg-[var(--ink-soft)] px-3 py-2 text-[var(--paper)]"
          required
        />
        <input
          value={translation}
          onChange={(e) => setTranslation(e.target.value)}
          placeholder="Translation (optional)"
          className="border border-[var(--line)] bg-[var(--ink-soft)] px-3 py-2 text-[var(--paper)]"
        />
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="border border-[var(--line)] bg-[var(--ink-soft)] px-3 py-2 text-[var(--paper)]"
        >
          <option value="terminology">Terminology</option>
          <option value="character">Character</option>
          <option value="geography">Geography</option>
          <option value="customs">Customs</option>
        </select>
        <button
          type="submit"
          disabled={busy}
          className="md:col-span-2 border border-[var(--gold)] bg-[rgba(197,161,94,0.14)] px-4 py-2 text-xs uppercase tracking-[0.14em] text-[var(--gold-bright)] disabled:opacity-50"
        >
          {busy ? "Saving…" : "Save draft"}
        </button>
      </form>

      {error ? <p className="mb-4 text-sm text-[var(--danger)]">{error}</p> : null}

      <ul className="space-y-3">
        {entries.map((e) => (
          <li key={e.id} className="border border-[var(--line)] px-4 py-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-[var(--paper)]">
                  {e.term}{" "}
                  <span className="text-xs text-[var(--mist)]">
                    {e.dialect || e.language} · {e.category} · {e.approval_status}
                  </span>
                </p>
                <p className="mt-1 text-sm text-[var(--mist)]">{e.definition}</p>
                {e.translation ? (
                  <p className="mt-1 text-sm text-[var(--paper-dim)]">Translation · {e.translation}</p>
                ) : null}
                {e.example_sentence ? (
                  <p className="mt-1 text-sm text-[var(--mist-soft)]">{e.example_sentence}</p>
                ) : null}
              </div>
              {e.approval_status !== "approved" ? (
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => void onApprove(e.id)}
                  className="border border-[var(--teal)] px-3 py-1 text-[0.65rem] uppercase tracking-[0.14em] text-[var(--teal)]"
                >
                  Approve
                </button>
              ) : null}
            </div>
          </li>
        ))}
      </ul>
    </CoreShell>
  );
}
