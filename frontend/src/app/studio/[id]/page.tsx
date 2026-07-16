"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import {
  api,
  type Character,
  type GenerationJob,
  type Modality,
  type Project,
  type StudioSummary,
} from "@/lib/api";
import { EmptyState } from "@/components/EmptyState";
import { MediaPreview } from "@/components/MediaPreview";
import { SiteHeader } from "@/components/SiteHeader";

const TABS: { id: Modality | "review"; label: string; blurb: string }[] = [
  { id: "video", label: "Video", blurb: "Shot proxies with picture + sound bed" },
  { id: "voice", label: "Conversation", blurb: "Dialogue and character voice takes" },
  { id: "music", label: "Music", blurb: "Themes, beds, and instrumentals" },
  { id: "audio", label: "Sounds", blurb: "SFX and atmospheric hits" },
  { id: "image", label: "Image", blurb: "Frames, posters, storyboard stills" },
  { id: "review", label: "Review", blurb: "Approve, reject, or request changes" },
];

export default function ProjectStudioPage() {
  const params = useParams();
  const projectId = String(params.id);

  const [tab, setTab] = useState<Modality | "review">("video");

  const [project, setProject] = useState<Project | null>(null);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [jobs, setJobs] = useState<GenerationJob[]>([]);
  const [summary, setSummary] = useState<StudioSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [prompt, setPrompt] = useState("");
  const [duration, setDuration] = useState(4);
  const [dialogue, setDialogue] = useState("");
  const [characterName, setCharacterName] = useState("");
  const [busy, setBusy] = useState(false);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [p, c, g, s] = await Promise.all([
        api.getProject(projectId),
        api.listCharacters(projectId),
        api.listGenerations(projectId),
        api.studioSummary(projectId),
      ]);
      setProject(p);
      setCharacters(c);
      setJobs(g);
      setSummary(s);
      if (!selectedJobId && g[0]) setSelectedJobId(g[0].id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to open studio");
      setProject(null);
    } finally {
      setLoading(false);
    }
  }, [projectId, selectedJobId]);

  useEffect(() => {
    void load();
    // intentionally once / when project changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  const filtered = useMemo(() => {
    if (tab === "review") return jobs.filter((j) => j.status === "succeeded");
    return jobs.filter((j) => j.modality === tab);
  }, [jobs, tab]);

  const selected = jobs.find((j) => j.id === selectedJobId) ?? filtered[0] ?? null;

  async function onGenerate(e: FormEvent) {
    e.preventDefault();
    if (tab === "review") return;
    if (!prompt.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const lines = dialogue
        .split("\n")
        .map((l) => l.trim())
        .filter(Boolean);
      const job = await api.generate(projectId, {
        modality: tab,
        prompt: prompt.trim(),
        duration_seconds: duration,
        dialogue_lines: tab === "voice" && lines.length ? lines : undefined,
        character_name: characterName.trim() || undefined,
      });
      setPrompt("");
      setDialogue("");
      setSelectedJobId(job.id);
      const [g, s] = await Promise.all([
        api.listGenerations(projectId),
        api.studioSummary(projectId),
      ]);
      setJobs(g);
      setSummary(s);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed");
    } finally {
      setBusy(false);
    }
  }

  async function onReview(decision: "approve" | "reject" | "request_changes") {
    if (!selected) return;
    setBusy(true);
    setError(null);
    try {
      await api.review(projectId, selected.id, { decision, quality_score: decision === "approve" ? 8 : 5 });
      const s = await api.studioSummary(projectId);
      setSummary(s);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Review failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="min-h-screen pb-24">
      <SiteHeader />
      <div className="ac-container pt-8 md:pt-12">
        {loading ? (
          <p className="py-16 text-[0.8rem] tracking-[0.18em] text-[var(--mist)] uppercase">
            Powering studio…
          </p>
        ) : !project ? (
          <EmptyState
            title="Studio unavailable"
            description={error ?? "Project not found."}
            action={
              <Link href="/studio" className="ac-btn ac-btn-primary">
                Back to studio
              </Link>
            }
          />
        ) : (
          <>
            <div className="mb-8 animate-rise">
              <Link
                href="/studio"
                className="ac-display text-[0.68rem] tracking-[0.28em] text-[var(--mist)] uppercase transition hover:text-[var(--gold-bright)]"
              >
                ← Studio floor
              </Link>
              <h1 className="ac-display mt-4 text-[clamp(2rem,5vw,3.4rem)] tracking-tight">
                {project.name}
              </h1>
              <p className="ac-serif mt-3 max-w-2xl text-[var(--mist)]">
                Full production desk — generate media, listen/watch, and review takes.
              </p>
              {summary ? (
                <div className="mt-5 flex flex-wrap gap-x-6 gap-y-2 text-[0.68rem] tracking-[0.16em] text-[var(--mist-soft)] uppercase">
                  <span>Pending review · {summary.pending_review}</span>
                  <span>Approved · {summary.approved}</span>
                  <span>Spend · ${summary.spent.toFixed(2)}</span>
                  <span>Video · {summary.totals.video ?? 0}</span>
                  <span>Voice · {summary.totals.voice ?? 0}</span>
                  <span>Music · {summary.totals.music ?? 0}</span>
                </div>
              ) : null}
            </div>

            <div className="mb-8 flex flex-wrap gap-2 border-b border-[var(--line)] pb-3 animate-rise-delay">
              {TABS.map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => setTab(t.id)}
                  className={`ac-display px-3 py-2 text-[0.72rem] tracking-[0.16em] uppercase transition ${
                    tab === t.id
                      ? "text-[var(--gold-bright)]"
                      : "text-[var(--mist)] hover:text-[var(--paper)]"
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>

            {error ? <p className="mb-6 text-sm text-[var(--danger)]">{error}</p> : null}

            <div className="grid gap-10 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.05fr)]">
              <section className="animate-rise-delay">
                {tab !== "review" ? (
                  <form onSubmit={onGenerate} className="space-y-5 border border-[var(--line)] bg-[rgba(10,15,22,0.45)] p-5 md:p-6">
                    <div>
                      <p className="ac-display text-xl text-[var(--gold-bright)]">
                        {TABS.find((t) => t.id === tab)?.label}
                      </p>
                      <p className="ac-serif mt-1 text-sm text-[var(--mist)]">
                        {TABS.find((t) => t.id === tab)?.blurb}
                      </p>
                    </div>

                    <div>
                      <label className="ac-label" htmlFor="prompt">
                        Creative direction
                      </label>
                      <textarea
                        id="prompt"
                        value={prompt}
                        onChange={(e) => setPrompt(e.target.value)}
                        className="ac-textarea"
                        rows={4}
                        placeholder={
                          tab === "video"
                            ? "Wide shot of Kardokh walking through Kurdiya village at golden hour…"
                            : tab === "voice"
                              ? "Warm Kurdish narration about friendship and home…"
                              : tab === "music"
                                ? "Gentle children’s theme in major key, soft strings…"
                                : tab === "audio"
                                  ? "Soft footstep on dry earth, distant wind…"
                                  : "Character poster, Kurdish clothing, soft landscape light…"
                        }
                        required
                      />
                    </div>

                    {(tab === "video" || tab === "music") && (
                      <div>
                        <label className="ac-label" htmlFor="duration">
                          Duration (seconds)
                        </label>
                        <input
                          id="duration"
                          type="number"
                          min={1}
                          max={30}
                          value={duration}
                          onChange={(e) => setDuration(Number(e.target.value))}
                          className="ac-field"
                        />
                      </div>
                    )}

                    {tab === "voice" && (
                      <>
                        <div>
                          <label className="ac-label" htmlFor="character">
                            Character (optional)
                          </label>
                          <input
                            id="character"
                            list="cast"
                            value={characterName}
                            onChange={(e) => setCharacterName(e.target.value)}
                            className="ac-field"
                            placeholder="Kardokh"
                          />
                          <datalist id="cast">
                            {characters.map((c) => (
                              <option key={c.id} value={c.name} />
                            ))}
                          </datalist>
                        </div>
                        <div>
                          <label className="ac-label" htmlFor="dialogue">
                            Conversation lines (one per line)
                          </label>
                          <textarea
                            id="dialogue"
                            value={dialogue}
                            onChange={(e) => setDialogue(e.target.value)}
                            className="ac-textarea min-h-[7rem]"
                            placeholder={"Kardokh: Hello, my friend.\nKurdiya: Welcome home."}
                          />
                        </div>
                      </>
                    )}

                    <button type="submit" disabled={busy} className="ac-btn ac-btn-primary">
                      {busy ? "Rendering…" : `Generate ${tab}`}
                    </button>
                  </form>
                ) : (
                  <div className="border border-[var(--line)] bg-[rgba(10,15,22,0.45)] p-5 md:p-6">
                    <p className="ac-display text-xl text-[var(--gold-bright)]">Quality control</p>
                    <p className="ac-serif mt-2 text-sm text-[var(--mist)]">
                      Select a take on the right, then record the production decision.
                    </p>
                    <div className="mt-6 flex flex-wrap gap-3">
                      <button
                        type="button"
                        disabled={!selected || busy}
                        className="ac-btn ac-btn-primary"
                        onClick={() => void onReview("approve")}
                      >
                        Approve
                      </button>
                      <button
                        type="button"
                        disabled={!selected || busy}
                        className="ac-btn ac-btn-secondary"
                        onClick={() => void onReview("request_changes")}
                      >
                        Request changes
                      </button>
                      <button
                        type="button"
                        disabled={!selected || busy}
                        className="ac-btn ac-btn-ghost"
                        onClick={() => void onReview("reject")}
                      >
                        Reject
                      </button>
                    </div>
                    <Link
                      href={`/projects/${projectId}`}
                      className="mt-8 inline-block text-sm text-[var(--mist)] transition hover:text-[var(--gold-bright)]"
                    >
                      Open project desk →
                    </Link>
                  </div>
                )}
              </section>

              <section className="animate-rise-late">
                <div className="mb-4 flex items-end justify-between gap-3">
                  <h2 className="ac-display text-lg text-[var(--paper)]">Takes</h2>
                  <span className="text-[0.68rem] tracking-[0.14em] text-[var(--mist-soft)] uppercase">
                    {filtered.length} items
                  </span>
                </div>

                {selected ? (
                  <div className="mb-6">
                    <MediaPreview job={selected} />
                    <p className="ac-serif mt-3 text-sm text-[var(--mist)]">{selected.prompt}</p>
                    <p className="mt-2 text-[0.68rem] tracking-[0.14em] text-[var(--mist-soft)] uppercase">
                      {selected.modality} · {selected.status} · $
                      {(selected.actual_cost ?? 0).toFixed(2)}
                    </p>
                  </div>
                ) : null}

                {filtered.length === 0 ? (
                  <EmptyState
                    title="No takes yet"
                    description="Generate your first media asset for this bay. Outputs are stored in Art City object storage."
                  />
                ) : (
                  <ul className="max-h-[28rem] space-y-0 overflow-auto border-t border-[var(--line)]">
                    {filtered.map((j) => (
                      <li key={j.id}>
                        <button
                          type="button"
                          onClick={() => setSelectedJobId(j.id)}
                          className={`ac-row w-full py-4 text-left ${
                            selected?.id === j.id ? "bg-[rgba(197,161,94,0.06)]" : ""
                          }`}
                        >
                          <p className="ac-display text-[0.95rem] text-[var(--paper)] line-clamp-1">
                            {j.prompt}
                          </p>
                          <p className="mt-1 text-[0.68rem] tracking-[0.12em] text-[var(--mist-soft)] uppercase">
                            {j.modality} · {j.status}
                          </p>
                        </button>
                        <div className="ac-rule" />
                      </li>
                    ))}
                  </ul>
                )}
              </section>
            </div>
          </>
        )}
      </div>
    </main>
  );
}
