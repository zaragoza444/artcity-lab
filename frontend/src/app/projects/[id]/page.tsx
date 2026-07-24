"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api, type Character, type Project, type Script } from "@/lib/api";
import { EmptyState } from "@/components/EmptyState";
import { SiteHeader } from "@/components/SiteHeader";

export default function ProjectDetailPage() {
  const params = useParams();
  const projectId = String(params.id);

  const [project, setProject] = useState<Project | null>(null);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [scripts, setScripts] = useState<Script[]>([]);
  const [charName, setCharName] = useState("");
  const [charDescription, setCharDescription] = useState("");
  const [scriptTitle, setScriptTitle] = useState("");
  const [scriptBody, setScriptBody] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [savingChar, setSavingChar] = useState(false);
  const [savingScript, setSavingScript] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [p, c, s] = await Promise.all([
        api.getProject(projectId),
        api.listCharacters(projectId),
        api.listScripts(projectId),
      ]);
      setProject(p);
      setCharacters(c);
      setScripts(s);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load project");
      setProject(null);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function addCharacter(e: FormEvent) {
    e.preventDefault();
    if (!charName.trim()) return;
    setSavingChar(true);
    setError(null);
    try {
      await api.createCharacter(projectId, {
        name: charName.trim(),
        description: charDescription.trim() || undefined,
      });
      setCharName("");
      setCharDescription("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add character");
    } finally {
      setSavingChar(false);
    }
  }

  async function addScript(e: FormEvent) {
    e.preventDefault();
    if (!scriptTitle.trim() || !scriptBody.trim()) return;
    setSavingScript(true);
    setError(null);
    try {
      await api.createScript(projectId, {
        title: scriptTitle.trim(),
        body: scriptBody.trim(),
        language: "ku",
      });
      setScriptTitle("");
      setScriptBody("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add script");
    } finally {
      setSavingScript(false);
    }
  }

  return (
    <main className="min-h-screen pb-24">
      <SiteHeader />

      <div className="ac-container pt-10 md:pt-14">
        {loading ? (
          <p className="py-20 text-[0.8rem] tracking-[0.18em] text-[var(--mist)] uppercase">
            Opening project…
          </p>
        ) : !project ? (
          <div className="py-10">
            <EmptyState
              title="Project unavailable"
              description={error ?? "This production could not be opened."}
              action={
                <Link href="/projects" className="ac-btn ac-btn-primary">
                  Return to slate
                </Link>
              }
            />
          </div>
        ) : (
          <>
            <div className="mb-14 animate-rise">
              <Link
                href="/projects"
                className="ac-display text-[0.68rem] tracking-[0.28em] text-[var(--mist)] uppercase transition hover:text-[var(--gold-bright)]"
              >
                ← Production slate
              </Link>
              <h1 className="ac-display mt-5 max-w-4xl text-[clamp(2.4rem,6vw,4.2rem)] leading-[0.98] tracking-tight text-[var(--paper)]">
                {project.name}
              </h1>
              {project.description ? (
                <p className="ac-serif mt-5 max-w-2xl text-[1.1rem] leading-relaxed text-[var(--mist)]">
                  {project.description}
                </p>
              ) : null}
              <div className="mt-6 flex flex-wrap gap-x-8 gap-y-2 text-[0.68rem] tracking-[0.18em] text-[var(--mist-soft)] uppercase">
                <span>Status · {project.status}</span>
                <span>Characters · {characters.length}</span>
                <span>Scripts · {scripts.length}</span>
              </div>
              <div className="mt-7 flex flex-wrap gap-3">
                <Link href={`/cinema/${project.id}`} className="ac-btn ac-btn-primary">
                  Cinema
                </Link>
                <Link href={`/studio/${project.id}`} className="ac-btn ac-btn-secondary">
                  Studio
                </Link>
                <Link href={`/projects/${project.id}/data-bank`} className="ac-btn ac-btn-secondary">
                  Data Bank
                </Link>
                <Link href="/edit" className="ac-btn ac-btn-secondary">
                  Edit
                </Link>
                <Link href={`/publish/${project.id}`} className="ac-btn ac-btn-ghost">
                  Publish
                </Link>
              </div>
              <div className="ac-rule mt-10" />
            </div>

            {error ? <p className="mb-8 text-sm text-[var(--danger)]">{error}</p> : null}

            <section className="mb-20 animate-rise-delay">
              <div className="mb-8 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  <h2 className="ac-display text-2xl text-[var(--gold-bright)]">Character library</h2>
                  <p className="ac-serif mt-2 max-w-xl text-[var(--mist)]">
                    Permanent identities for consistent faces, costume, and voice across the episode.
                  </p>
                </div>
              </div>

              <form
                onSubmit={addCharacter}
                className="mb-10 grid gap-5 border border-[var(--line)] bg-[rgba(10,15,22,0.4)] p-5 md:grid-cols-[1fr_1fr_auto] md:p-6"
              >
                <div>
                  <label className="ac-label" htmlFor="char-name">
                    Character
                  </label>
                  <input
                    id="char-name"
                    value={charName}
                    onChange={(e) => setCharName(e.target.value)}
                    placeholder="Kardokh"
                    className="ac-field"
                    required
                  />
                </div>
                <div>
                  <label className="ac-label" htmlFor="char-desc">
                    Identity notes
                  </label>
                  <input
                    id="char-desc"
                    value={charDescription}
                    onChange={(e) => setCharDescription(e.target.value)}
                    placeholder="Costume, palette, expression rules"
                    className="ac-field"
                  />
                </div>
                <div className="flex items-end">
                  <button
                    type="submit"
                    disabled={savingChar}
                    className="ac-btn ac-btn-secondary w-full md:w-auto"
                  >
                    {savingChar ? "Saving…" : "Register"}
                  </button>
                </div>
              </form>

              {characters.length === 0 ? (
                <EmptyState
                  title="Cast not registered"
                  description="Add Kardokh, Kurdiya, and supporting roles before generating storyboards or shots."
                />
              ) : (
                <ul>
                  {characters.map((c, i) => (
                    <li key={c.id} className="ac-row grid grid-cols-[auto_1fr] gap-5 py-5">
                      <span className="ac-display text-[0.72rem] tracking-[0.14em] text-[var(--mist-soft)]">
                        {String(i + 1).padStart(2, "0")}
                      </span>
                      <div>
                        <p className="ac-display text-xl text-[var(--paper)]">{c.name}</p>
                        {c.description ? (
                          <p className="ac-serif mt-1 text-[var(--mist)]">{c.description}</p>
                        ) : null}
                      </div>
                      <div className="ac-rule col-span-2" />
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section className="animate-rise-late">
              <div className="mb-8">
                <h2 className="ac-display text-2xl text-[var(--gold-bright)]">Script desk</h2>
                <p className="ac-serif mt-2 max-w-xl text-[var(--mist)]">
                  Kurdish drafts for scene breakdown, dialogue timing, and prompt generation.
                </p>
              </div>

              <form
                onSubmit={addScript}
                className="mb-12 space-y-5 border border-[var(--line)] bg-[rgba(10,15,22,0.4)] p-5 md:p-6"
              >
                <div>
                  <label className="ac-label" htmlFor="script-title">
                    Script title
                  </label>
                  <input
                    id="script-title"
                    value={scriptTitle}
                    onChange={(e) => setScriptTitle(e.target.value)}
                    placeholder="Episode 01 — Master draft"
                    className="ac-field"
                    required
                  />
                </div>
                <div>
                  <label className="ac-label" htmlFor="script-body">
                    Body
                  </label>
                  <textarea
                    id="script-body"
                    value={scriptBody}
                    onChange={(e) => setScriptBody(e.target.value)}
                    placeholder="Write or paste the Kurdish script…"
                    rows={9}
                    className="ac-textarea"
                    required
                  />
                </div>
                <button type="submit" disabled={savingScript} className="ac-btn ac-btn-primary">
                  {savingScript ? "Saving…" : "Save to archive"}
                </button>
              </form>

              {scripts.length === 0 ? (
                <EmptyState
                  title="No scripts on desk"
                  description="Save the first draft to begin scene and shot planning for the pilot."
                />
              ) : (
                <ul className="space-y-10">
                  {scripts.map((s) => (
                    <li key={s.id}>
                      <div className="ac-rule mb-6" />
                      <div className="flex flex-wrap items-baseline justify-between gap-3">
                        <p className="ac-display text-2xl text-[var(--paper)]">{s.title}</p>
                        <span className="ac-display text-[0.68rem] tracking-[0.2em] text-[var(--mist-soft)] uppercase">
                          Language · {s.language}
                        </span>
                      </div>
                      <pre className="ac-serif mt-5 whitespace-pre-wrap text-[1.02rem] leading-[1.8] text-[var(--paper-dim)]">
                        {s.body}
                      </pre>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </>
        )}
      </div>
    </main>
  );
}
