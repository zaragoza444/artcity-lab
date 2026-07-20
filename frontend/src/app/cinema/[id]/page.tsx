"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import {
  api,
  mediaAbsolute,
  type CinemaDeliverable,
  type CinemaPackage,
  type Project,
} from "@/lib/api";
import { EmptyState } from "@/components/EmptyState";
import { SiteHeader } from "@/components/SiteHeader";

function DeliverableCard({ item }: { item: CinemaDeliverable }) {
  const media = mediaAbsolute(item.mp4_url || item.media_url);
  const audio = mediaAbsolute(item.audio_url);
  const isVisual = item.modality === "video" || item.modality === "image";
  const isMp4 = Boolean(item.is_mp4 || item.file?.endsWith(".mp4") || item.mp4_url);

  return (
    <article className="border border-[var(--line)] bg-[rgba(10,15,22,0.5)] p-4 md:p-5">
      <div className="mb-3 flex items-baseline justify-between gap-3">
        <p className="ac-display text-[var(--paper)]">{item.label ?? item.role}</p>
        <span className="ac-display text-[0.65rem] tracking-[0.16em] text-[var(--mist-soft)] uppercase">
          {item.variant ? `${item.variant} · ` : ""}
          {isMp4 ? "MP4 · " : ""}
          {item.aspect ?? item.modality}
        </span>
      </div>
      {isVisual && media && isMp4 ? (
        <video
          controls
          src={media}
          className={`w-full border border-[var(--line)] bg-black object-cover ${
            item.aspect === "9:16"
              ? "aspect-[9/16] max-h-[28rem] mx-auto"
              : item.aspect === "1:1"
                ? "aspect-square max-h-[22rem] mx-auto"
                : "aspect-video"
          }`}
        />
      ) : null}
      {isVisual && media && !isMp4 ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={media}
          alt={item.label ?? "Cinema deliverable"}
          className={`w-full border border-[var(--line)] bg-black object-cover ${
            item.aspect === "9:16"
              ? "aspect-[9/16] max-h-[28rem] mx-auto"
              : item.aspect === "1:1"
                ? "aspect-square max-h-[22rem] mx-auto"
                : "aspect-video"
          }`}
        />
      ) : null}
      {(audio || (!isVisual && media)) && (
        <audio controls src={audio ?? media ?? undefined} className="mt-3 w-full">
          Audio preview
        </audio>
      )}
      {item.role === "voiceover" && item.transcript?.segments?.length ? (
        <div className="mt-4 border-t border-[var(--line)] pt-3">
          <p className="text-[0.65rem] uppercase tracking-[0.14em] text-[var(--mist)]">
            VO transcript · {item.transcript.dialect} · conf {item.transcript.average_confidence}
          </p>
          <p className="mt-2 text-sm text-[var(--paper-dim)]">
            {item.transcript.segments
              .slice(0, 3)
              .map((s) => s.text)
              .join(" ")}
            {item.transcript.segments.length > 3 ? "…" : ""}
          </p>
          {item.transcript_job_id ? (
            <p className="mt-1 font-mono text-[0.65rem] text-[var(--mist-soft)]">
              ASR {item.transcript_job_id.slice(0, 8)}
            </p>
          ) : null}
        </div>
      ) : null}
    </article>
  );
}

export default function CinemaProjectPage() {
  const params = useParams();
  const projectId = String(params.id);

  const [project, setProject] = useState<Project | null>(null);
  const [packages, setPackages] = useState<CinemaPackage[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [campaign, setCampaign] = useState("");
  const [brief, setBrief] = useState("");
  const [cta, setCta] = useState("Watch the story");
  const [vo, setVo] = useState("");
  const [musicStyle, setMusicStyle] = useState<"epic" | "warm" | "pulse" | "soft">("epic");
  const [duration, setDuration] = useState(15);
  const [dialect, setDialect] = useState("sorani");
  const [characterKey, setCharacterKey] = useState("");
  const [channels, setChannels] = useState<string[]>([
    "broadcast",
    "social_vertical",
    "social_square",
  ]);
  const [variants, setVariants] = useState<string[]>(["A"]);
  const [deliveryTargets, setDeliveryTargets] = useState<string[]>([
    "youtube",
    "meta_stories",
    "broadcast_tv",
  ]);
  const [musicGain, setMusicGain] = useState(0);
  const [voiceGain, setVoiceGain] = useState(0);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [p, pkgs] = await Promise.all([
        api.getProject(projectId),
        api.listCinemaPackages(projectId),
      ]);
      setProject(p);
      setPackages(pkgs);
      if (!activeId && pkgs[0]) setActiveId(pkgs[0].package_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to open cinema");
      setProject(null);
    } finally {
      setLoading(false);
    }
  }, [projectId, activeId]);

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  const active = useMemo(
    () => packages.find((p) => p.package_id === activeId) ?? packages[0] ?? null,
    [packages, activeId]
  );

  async function onRender(e: FormEvent) {
    e.preventDefault();
    if (!campaign.trim() || !brief.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const pkg = await api.createCinemaPackage(projectId, {
        campaign: campaign.trim(),
        brief: brief.trim(),
        cta: cta.trim() || "Discover more",
        brand: "Art City",
        voiceover_script: vo.trim() || undefined,
        music_style: musicStyle,
        duration_seconds: duration,
        initiated_by: "art-city-producer",
        dialect,
        character_key: characterKey || undefined,
        character_name: characterKey
          ? characterKey === "kardokh"
            ? "Kardokh"
            : characterKey === "kurdiya"
              ? "Kurdiya"
              : undefined
          : undefined,
        channels,
        variants,
        delivery_targets: deliveryTargets,
      });
      setActiveId(pkg.package_id);
      if (pkg.timeline?.mix) {
        setMusicGain(Number(pkg.timeline.mix.music_gain_db ?? 0));
        setVoiceGain(Number(pkg.timeline.mix.voice_gain_db ?? 0));
      }
      setCampaign("");
      setBrief("");
      const pkgs = await api.listCinemaPackages(projectId);
      setPackages(pkgs);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Package render failed");
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
            Opening cinema…
          </p>
        ) : !project ? (
          <EmptyState
            title="Cinema unavailable"
            description={error ?? "Project not found."}
            action={
              <Link href="/cinema" className="ac-btn ac-btn-primary">
                Back to cinema
              </Link>
            }
          />
        ) : (
          <>
            <div className="mb-10 animate-rise">
              <Link
                href="/cinema"
                className="ac-display text-[0.68rem] tracking-[0.28em] text-[var(--mist)] uppercase transition hover:text-[var(--gold-bright)]"
              >
                ← Cinema floor
              </Link>
              <h1 className="ac-display mt-4 text-[clamp(2rem,5vw,3.6rem)] tracking-tight">
                {project.name}
              </h1>
              <p className="ac-serif mt-3 max-w-2xl text-[1.05rem] text-[var(--mist)]">
                Art City Cinema builds complete advertising campaigns with technical QC —
                not single Studio takes.
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <Link href={`/publish/${projectId}`} className="ac-btn ac-btn-primary">
                  Publish masters
                </Link>
                <Link href={`/studio/${projectId}`} className="ac-btn ac-btn-secondary">
                  Art City Studio
                </Link>
                <Link href={`/projects/${projectId}`} className="ac-btn ac-btn-ghost">
                  Project desk
                </Link>
              </div>
            </div>

            {error ? <p className="mb-6 text-sm text-[var(--danger)]">{error}</p> : null}

            <div className="grid gap-10 lg:grid-cols-[minmax(0,0.95fr)_minmax(0,1.15fr)]">
              <form
                onSubmit={onRender}
                className="space-y-5 border border-[var(--line)] bg-[rgba(10,15,22,0.5)] p-5 md:p-6 animate-rise-delay"
              >
                <div>
                  <p className="ac-display text-xl text-[var(--gold-bright)]">Campaign brief</p>
                  <p className="ac-serif mt-1 text-sm text-[var(--mist)]">
                    One render builds the full cinema advertising set.
                  </p>
                </div>
                <div>
                  <label className="ac-label" htmlFor="campaign">
                    Campaign name
                  </label>
                  <input
                    id="campaign"
                    className="ac-field"
                    value={campaign}
                    onChange={(e) => setCampaign(e.target.value)}
                    placeholder="Kardokh & Kurdiya · Homecoming"
                    required
                  />
                </div>
                <div>
                  <label className="ac-label" htmlFor="brief">
                    Creative brief
                  </label>
                  <textarea
                    id="brief"
                    className="ac-textarea"
                    rows={5}
                    value={brief}
                    onChange={(e) => setBrief(e.target.value)}
                    placeholder="Golden-hour village paths, childhood wonder, warm family reunion… cinematic, emotional, premium advertising tone."
                    required
                  />
                </div>
                <div>
                  <label className="ac-label" htmlFor="cta">
                    Call to action
                  </label>
                  <input
                    id="cta"
                    className="ac-field"
                    value={cta}
                    onChange={(e) => setCta(e.target.value)}
                    placeholder="Watch the story"
                  />
                </div>
                <div>
                  <label className="ac-label" htmlFor="vo">
                    Voiceover script (optional)
                  </label>
                  <textarea
                    id="vo"
                    className="ac-textarea min-h-[6rem]"
                    value={vo}
                    onChange={(e) => setVo(e.target.value)}
                    placeholder="In every homecoming, a new adventure begins…"
                  />
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <label className="ac-label" htmlFor="style">
                      Music style
                    </label>
                    <select
                      id="style"
                      className="ac-field"
                      value={musicStyle}
                      onChange={(e) =>
                        setMusicStyle(e.target.value as "epic" | "warm" | "pulse" | "soft")
                      }
                    >
                      <option value="epic">Epic cinematic</option>
                      <option value="warm">Warm emotional</option>
                      <option value="pulse">Modern pulse</option>
                      <option value="soft">Soft intimate</option>
                    </select>
                  </div>
                  <div>
                    <label className="ac-label" htmlFor="duration">
                      Spot length (sec)
                    </label>
                    <input
                      id="duration"
                      type="number"
                      min={5}
                      max={60}
                      className="ac-field"
                      value={duration}
                      onChange={(e) => setDuration(Number(e.target.value))}
                    />
                  </div>
                  <div>
                    <label className="ac-label" htmlFor="dialect">
                      Kurdish dialect
                    </label>
                    <select
                      id="dialect"
                      className="ac-field"
                      value={dialect}
                      onChange={(e) => setDialect(e.target.value)}
                    >
                      <option value="sorani">Sorani</option>
                      <option value="badini">Badini</option>
                      <option value="kurmanji">Kurmanji</option>
                    </select>
                  </div>
                  <div>
                    <label className="ac-label" htmlFor="character">
                      Character focus
                    </label>
                    <select
                      id="character"
                      className="ac-field"
                      value={characterKey}
                      onChange={(e) => setCharacterKey(e.target.value)}
                    >
                      <option value="">Brand general</option>
                      <option value="kardokh">Kardokh</option>
                      <option value="kurdiya">Kurdiya</option>
                    </select>
                  </div>
                </div>
                <fieldset className="space-y-2">
                  <legend className="ac-label">Advertising channels</legend>
                  {[
                    ["broadcast", "Broadcast 16:9"],
                    ["social_vertical", "Social vertical 9:16"],
                    ["social_square", "Social square 1:1"],
                  ].map(([id, label]) => (
                    <label key={id} className="flex items-center gap-2 text-sm text-[var(--mist)]">
                      <input
                        type="checkbox"
                        checked={channels.includes(id)}
                        onChange={(e) => {
                          setChannels((prev) =>
                            e.target.checked
                              ? [...prev, id]
                              : prev.filter((c) => c !== id)
                          );
                        }}
                      />
                      {label}
                    </label>
                  ))}
                </fieldset>
                <fieldset className="space-y-2">
                  <legend className="ac-label">A/B variants</legend>
                  {[
                    ["A", "A · Control"],
                    ["B", "B · Alt CTA"],
                    ["C", "C · Alt music"],
                  ].map(([id, label]) => (
                    <label key={id} className="flex items-center gap-2 text-sm text-[var(--mist)]">
                      <input
                        type="checkbox"
                        checked={variants.includes(id)}
                        onChange={(e) => {
                          setVariants((prev) => {
                            const next = e.target.checked
                              ? [...prev, id]
                              : prev.filter((c) => c !== id);
                            return next.length ? next : ["A"];
                          });
                        }}
                      />
                      {label}
                    </label>
                  ))}
                </fieldset>
                <fieldset className="space-y-2">
                  <legend className="ac-label">World delivery targets</legend>
                  {[
                    ["youtube", "YouTube"],
                    ["meta_feed", "Meta Feed"],
                    ["meta_stories", "Meta / TikTok Stories"],
                    ["broadcast_tv", "Broadcast / TV"],
                    ["ctv", "CTV"],
                  ].map(([id, label]) => (
                    <label key={id} className="flex items-center gap-2 text-sm text-[var(--mist)]">
                      <input
                        type="checkbox"
                        checked={deliveryTargets.includes(id)}
                        onChange={(e) => {
                          setDeliveryTargets((prev) =>
                            e.target.checked
                              ? [...prev, id]
                              : prev.filter((c) => c !== id)
                          );
                        }}
                      />
                      {label}
                    </label>
                  ))}
                </fieldset>
                <button
                  type="submit"
                  disabled={busy || channels.length === 0}
                  className="ac-btn ac-btn-primary"
                >
                  {busy ? "Rendering package…" : "Render full advertising package"}
                </button>
              </form>

              <section className="animate-rise-late">
                <div className="mb-5 flex items-end justify-between gap-3">
                  <h2 className="ac-display text-lg text-[var(--paper)]">Packages</h2>
                  <span className="text-[0.68rem] tracking-[0.14em] text-[var(--mist-soft)] uppercase">
                    {packages.length} rendered
                  </span>
                </div>

                {packages.length === 0 ? (
                  <EmptyState
                    title="No cinema packages yet"
                    description="Fill the campaign brief and render. Art City will deliver broadcast, vertical, square, music, VO, and end card."
                  />
                ) : (
                  <>
                    <ul className="mb-8 border-t border-[var(--line)]">
                      {packages.map((pkg) => (
                        <li key={pkg.package_id}>
                          <button
                            type="button"
                            onClick={() => setActiveId(pkg.package_id)}
                            className={`ac-row w-full py-4 text-left ${
                              active?.package_id === pkg.package_id
                                ? "bg-[rgba(197,161,94,0.06)]"
                                : ""
                            }`}
                          >
                            <p className="ac-display text-lg">{pkg.campaign}</p>
                            <p className="mt-1 text-[0.68rem] tracking-[0.12em] text-[var(--mist-soft)] uppercase">
                              {pkg.duration_seconds}s · {pkg.music_style} · $
                              {pkg.total_cost.toFixed(2)}
                            </p>
                          </button>
                          <div className="ac-rule" />
                        </li>
                      ))}
                    </ul>

                    {active ? (
                      <div className="space-y-8">
                        <div className="mb-2">
                          <p className="ac-display text-[0.68rem] tracking-[0.2em] text-[var(--gold)] uppercase">
                            Art City Cinema
                          </p>
                          <p className="ac-display mt-2 text-2xl text-[var(--gold-bright)]">
                            {active.campaign}
                          </p>
                          <p className="ac-serif mt-2 text-[var(--mist)]">{active.brief}</p>
                          <p className="mt-3 text-[0.68rem] tracking-[0.14em] text-[var(--mist-soft)] uppercase">
                            CTA · {active.cta} · {active.duration_seconds}s · $
                            {active.total_cost.toFixed(2)} ·{" "}
                            {active.production_time_seconds ?? "—"}s render
                          </p>
                          {active.variants?.length ? (
                            <p className="mt-2 text-sm text-[var(--mist)]">
                              Variants{" "}
                              {active.variants.map((v) => v.id).join(" · ")}
                              {active.delivery_targets?.length
                                ? ` · Delivery ${active.delivery_targets
                                    .map((d) => d.label || d.id)
                                    .join(", ")}`
                                : ""}
                            </p>
                          ) : null}
                          {active.timeline?.clips?.length ? (
                            <div className="mt-6 border border-[var(--line)] p-4">
                              <p className="ac-display text-[0.68rem] tracking-[0.16em] text-[var(--gold)] uppercase">
                                Finishing timeline
                              </p>
                              <ul className="mt-3 space-y-2">
                                {active.timeline.clips.map((clip) => (
                                  <li
                                    key={clip.id}
                                    className="flex justify-between gap-3 text-sm text-[var(--mist)]"
                                  >
                                    <span>
                                      {clip.track} · {clip.label}
                                    </span>
                                    <span className="font-mono text-[0.7rem] text-[var(--mist-soft)]">
                                      {clip.start.toFixed(1)}–{clip.end.toFixed(1)}s
                                    </span>
                                  </li>
                                ))}
                              </ul>
                              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                                <label className="text-xs text-[var(--mist)]">
                                  Music gain (dB)
                                  <input
                                    type="number"
                                    className="ac-field mt-1"
                                    value={musicGain}
                                    onChange={(e) => setMusicGain(Number(e.target.value))}
                                  />
                                </label>
                                <label className="text-xs text-[var(--mist)]">
                                  Voice gain (dB)
                                  <input
                                    type="number"
                                    className="ac-field mt-1"
                                    value={voiceGain}
                                    onChange={(e) => setVoiceGain(Number(e.target.value))}
                                  />
                                </label>
                              </div>
                              <button
                                type="button"
                                className="ac-btn ac-btn-secondary mt-3"
                                onClick={async () => {
                                  try {
                                    const updated = await api.updateCinemaTimeline(
                                      projectId,
                                      active.package_id,
                                      {
                                        music_gain_db: musicGain,
                                        voice_gain_db: voiceGain,
                                        duck_music_under_vo: true,
                                      }
                                    );
                                    setPackages((prev) =>
                                      prev.map((p) =>
                                        p.package_id === updated.package_id ? updated : p
                                      )
                                    );
                                  } catch (err) {
                                    setError(
                                      err instanceof Error ? err.message : "Timeline update failed"
                                    );
                                  }
                                }}
                              >
                                Save mix
                              </button>
                            </div>
                          ) : null}
                          <div className="mt-4 flex flex-wrap gap-2">
                            <span
                              className={`ac-display text-[0.68rem] tracking-[0.14em] uppercase ${
                                active.validation_passed
                                  ? "text-emerald-300"
                                  : "text-[var(--danger)]"
                              }`}
                            >
                              QC {active.validation_passed ? "passed" : "failed"}
                            </span>
                            <a
                              href={api.cinemaZipUrl(projectId, active.package_id)}
                              className="ac-btn ac-btn-primary"
                            >
                              Download ZIP
                            </a>
                            <a
                              href={api.cinemaManifestUrl(projectId, active.package_id)}
                              target="_blank"
                              rel="noreferrer"
                              className="ac-btn ac-btn-secondary"
                            >
                              Manifest
                            </a>
                            <a
                              href={api.cinemaValidationUrl(projectId, active.package_id)}
                              target="_blank"
                              rel="noreferrer"
                              className="ac-btn ac-btn-ghost"
                            >
                              Validation JSON
                            </a>
                            <button
                              type="button"
                              className="ac-btn ac-btn-ghost"
                              disabled={busy}
                              onClick={async () => {
                                setBusy(true);
                                try {
                                  const refreshed = await api.validateCinemaPackage(
                                    projectId,
                                    active.package_id
                                  );
                                  setPackages((prev) =>
                                    prev.map((p) =>
                                      p.package_id === refreshed.package_id ? refreshed : p
                                    )
                                  );
                                } catch (err) {
                                  setError(
                                    err instanceof Error ? err.message : "Revalidate failed"
                                  );
                                } finally {
                                  setBusy(false);
                                }
                              }}
                            >
                              Re-run QC
                            </button>
                          </div>
                        </div>

                        {active.validation ? (
                          <div className="border border-[var(--line)] p-5">
                            <h3 className="ac-display text-lg text-[var(--paper)]">
                              Technical validation
                            </h3>
                            <p className="mt-2 text-sm text-[var(--mist)]">
                              Completeness:{" "}
                              {active.validation.completeness?.passed ? "all six outputs" : "incomplete"}
                            </p>
                            <ul className="mt-4 space-y-3">
                              {active.validation.deliverables.map((d) => (
                                <li key={d.role} className="border-t border-[var(--line)] pt-3">
                                  <div className="flex items-baseline justify-between gap-3">
                                    <p className="ac-display text-[var(--paper)]">{d.role}</p>
                                    <span
                                      className={`text-[0.65rem] tracking-[0.14em] uppercase ${
                                        d.passed ? "text-emerald-300" : "text-[var(--danger)]"
                                      }`}
                                    >
                                      {d.passed ? "pass" : "fail"}
                                    </span>
                                  </div>
                                  <ul className="mt-2 space-y-1">
                                    {d.checks.map((c) => (
                                      <li
                                        key={`${d.role}-${c.id}`}
                                        className={`text-xs ${
                                          c.passed ? "text-[var(--mist-soft)]" : "text-[var(--danger)]"
                                        }`}
                                      >
                                        {c.passed ? "✓" : "✗"} {c.label}
                                        {!c.passed
                                          ? ` · expected ${String(c.expected)} / actual ${String(c.actual)}`
                                          : ""}
                                      </li>
                                    ))}
                                  </ul>
                                </li>
                              ))}
                            </ul>
                          </div>
                        ) : null}

                        <div className="grid gap-5">
                          {active.deliverables.map((d) => (
                            <DeliverableCard key={d.job_id} item={d} />
                          ))}
                        </div>
                      </div>
                    ) : null}
                  </>
                )}
              </section>
            </div>
          </>
        )}
      </div>
    </main>
  );
}
