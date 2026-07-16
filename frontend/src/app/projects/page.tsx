"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { api, type Project } from "@/lib/api";
import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";
import { SiteHeader } from "@/components/SiteHeader";

function formatDate(value: string) {
  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(value));
  } catch {
    return value;
  }
}

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await api.listProjects();
      setProjects(data);
      if (data.length === 0) setShowForm(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load projects");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setSaving(true);
    setError(null);
    try {
      await api.createProject({
        name: name.trim(),
        description: description.trim() || undefined,
      });
      setName("");
      setDescription("");
      setShowForm(false);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create project");
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="min-h-screen pb-20">
      <SiteHeader />

      <div className="ac-container pt-10 md:pt-14">
        <PageHeader
          eyebrow="Production slate"
          title="Projects"
          description="Commission-grade productions under Art City control — characters, scripts, generations, and masters."
          actions={
            <button
              type="button"
              className="ac-btn ac-btn-primary"
              onClick={() => setShowForm((v) => !v)}
            >
              {showForm ? "Close" : "New project"}
            </button>
          }
        />

        {showForm ? (
          <form
            onSubmit={onCreate}
            className="mb-14 space-y-6 border border-[var(--line)] bg-[rgba(10,15,22,0.45)] p-6 md:p-8 animate-rise-delay"
          >
            <div>
              <label className="ac-label" htmlFor="project-name">
                Project title
              </label>
              <input
                id="project-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Kardokh & Kurdiya — 365 Days"
                className="ac-field text-lg"
                required
                autoFocus
              />
            </div>
            <div>
              <label className="ac-label" htmlFor="project-description">
                Production note
              </label>
              <textarea
                id="project-description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Episode intent, tone, and delivery targets"
                rows={3}
                className="ac-textarea min-h-[6rem]"
              />
            </div>
            <div className="flex flex-wrap items-center gap-3 pt-1">
              <button type="submit" disabled={saving} className="ac-btn ac-btn-primary">
                {saving ? "Creating…" : "Create project"}
              </button>
              <button
                type="button"
                className="ac-btn ac-btn-ghost"
                onClick={() => setShowForm(false)}
              >
                Cancel
              </button>
            </div>
            {error ? <p className="text-sm text-[var(--danger)]">{error}</p> : null}
          </form>
        ) : null}

        {!showForm && error ? (
          <p className="mb-6 text-sm text-[var(--danger)]">{error}</p>
        ) : null}

        <section className="animate-rise-late">
          {loading ? (
            <div className="space-y-4 py-8">
              <div className="h-px w-full bg-[var(--line)]" />
              <p className="text-[0.8rem] tracking-[0.18em] text-[var(--mist)] uppercase">
                Loading slate…
              </p>
            </div>
          ) : projects.length === 0 ? (
            <EmptyState
              title="Your slate is empty"
              description="Open the first Art City production. Character libraries, Kurdish scripts, and review workflows start here."
              action={
                <button
                  type="button"
                  className="ac-btn ac-btn-primary"
                  onClick={() => setShowForm(true)}
                >
                  Begin first project
                </button>
              }
            />
          ) : (
            <ul className="border-t border-[var(--line)]">
              {projects.map((p, index) => (
                <li key={p.id} className="ac-row">
                  <Link
                    href={`/projects/${p.id}`}
                    className="group grid grid-cols-[auto_1fr_auto] items-baseline gap-4 py-7 md:gap-8"
                  >
                    <span className="ac-display w-8 text-[0.75rem] tracking-[0.14em] text-[var(--mist-soft)]">
                      {String(index + 1).padStart(2, "0")}
                    </span>
                    <div className="min-w-0">
                      <p className="ac-display text-2xl tracking-tight text-[var(--paper)] transition group-hover:text-[var(--gold-bright)]">
                        {p.name}
                      </p>
                      {p.description ? (
                        <p className="ac-serif mt-2 max-w-2xl text-[0.98rem] text-[var(--mist)]">
                          {p.description}
                        </p>
                      ) : null}
                      <p className="mt-3 text-[0.7rem] tracking-[0.14em] text-[var(--mist-soft)] uppercase">
                        Updated {formatDate(p.updated_at)}
                      </p>
                    </div>
                    <span className="ac-display shrink-0 text-[0.68rem] tracking-[0.2em] text-[var(--mist)] uppercase">
                      {p.status}
                    </span>
                  </Link>
                  <div className="ac-rule" />
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </main>
  );
}
