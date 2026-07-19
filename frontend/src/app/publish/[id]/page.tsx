"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import {
  api,
  mediaAbsolute,
  withAccessToken,
  type CinemaPackage,
  type Project,
  type Publication,
  type PublicationMaster,
} from "@/lib/api";
import { EmptyState } from "@/components/EmptyState";
import { SiteHeader } from "@/components/SiteHeader";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function statusTone(status: string) {
  if (status === "published" || status === "ready") return "text-emerald-300";
  if (status === "blocked" || status === "failed") return "text-[var(--danger)]";
  return "text-[var(--gold-bright)]";
}

function MasterCard({ master }: { master: PublicationMaster }) {
  const media = mediaAbsolute(master.media_url);
  const audio = mediaAbsolute(master.audio_url);
  const visual = master.modality === "video" || master.modality === "image";

  return (
    <article className="border border-[var(--line)] bg-[rgba(10,15,22,0.5)] p-4">
      <div className="mb-3 flex items-baseline justify-between gap-3">
        <p className="ac-display text-[var(--paper)]">{master.label}</p>
        <span className="text-[0.65rem] tracking-[0.14em] text-[var(--mist-soft)] uppercase">
          {master.aspect ?? master.modality}
        </span>
      </div>
      {visual && media ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={media}
          alt={master.label}
          className={`w-full border border-[var(--line)] bg-black object-cover ${
            master.aspect === "9:16"
              ? "aspect-[9/16] max-h-80 mx-auto"
              : master.aspect === "1:1"
                ? "aspect-square max-h-72 mx-auto"
                : "aspect-video"
          }`}
        />
      ) : null}
      {(audio || (!visual && media)) && (
        <audio controls className="mt-3 w-full" src={audio ?? media ?? undefined} />
      )}
      {master.checksum_sha256 ? (
        <p className="mt-3 break-all font-mono text-[0.65rem] text-[var(--mist-soft)]">
          sha256 {master.checksum_sha256.slice(0, 24)}…
        </p>
      ) : null}
    </article>
  );
}

export default function PublishProjectPage() {
  const params = useParams();
  const projectId = String(params.id);

  const [project, setProject] = useState<Project | null>(null);
  const [packages, setPackages] = useState<CinemaPackage[]>([]);
  const [publications, setPublications] = useState<Publication[]>([]);
  const [selectedPackage, setSelectedPackage] = useState("");
  const [channel, setChannel] = useState("art_city_channel");
  const [note, setNote] = useState("");
  const [activeId, setActiveId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [p, pkgs, pubs] = await Promise.all([
        api.getProject(projectId),
        api.listCinemaPackages(projectId),
        api.listPublications(projectId),
      ]);
      setProject(p);
      setPackages(pkgs);
      setPublications(pubs);
      if (!selectedPackage && pkgs[0]) setSelectedPackage(pkgs[0].package_id);
      if (!activeId && pubs[0]) setActiveId(pubs[0].publication_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to open publish");
      setProject(null);
    } finally {
      setLoading(false);
    }
  }, [projectId, selectedPackage, activeId]);

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  const active = useMemo(
    () => publications.find((p) => p.publication_id === activeId) ?? publications[0] ?? null,
    [publications, activeId]
  );

  async function onPackage(e: FormEvent) {
    e.preventDefault();
    if (!selectedPackage) return;
    setBusy(true);
    setError(null);
    try {
      const pub = await api.createPublication(projectId, {
        cinema_package_id: selectedPackage,
        channel,
        auto_approve_missing: true,
        publisher_note: note.trim() || undefined,
      });
      setActiveId(pub.publication_id);
      setPublications(await api.listPublications(projectId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Packaging failed");
    } finally {
      setBusy(false);
    }
  }

  async function onRelease() {
    if (!active) return;
    setBusy(true);
    setError(null);
    try {
      const pub = await api.finalizePublish(projectId, active.publication_id);
      setActiveId(pub.publication_id);
      setPublications(await api.listPublications(projectId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Publish failed");
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
            Opening delivery desk…
          </p>
        ) : !project ? (
          <EmptyState
            title="Publish unavailable"
            description={error ?? "Project not found."}
            action={
              <Link href="/publish" className="ac-btn ac-btn-primary">
                Back to publish
              </Link>
            }
          />
        ) : (
          <>
            <div className="mb-10 animate-rise">
              <Link
                href="/publish"
                className="ac-display text-[0.68rem] tracking-[0.28em] text-[var(--mist)] uppercase transition hover:text-[var(--gold-bright)]"
              >
                ← Publish floor
              </Link>
              <h1 className="ac-display mt-4 text-[clamp(2rem,5vw,3.5rem)] tracking-tight">
                {project.name}
              </h1>
              <p className="ac-serif mt-3 max-w-2xl text-[var(--mist)]">
                Package approved cinema masters into a checksummed Art City delivery for broadcast
                and social release.
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <Link href={`/cinema/${projectId}`} className="ac-btn ac-btn-secondary">
                  Cinema packages
                </Link>
                <Link href={`/studio/${projectId}`} className="ac-btn ac-btn-ghost">
                  Media studio
                </Link>
              </div>
            </div>

            {error ? <p className="mb-6 text-sm text-[var(--danger)]">{error}</p> : null}

            <div className="grid gap-10 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.2fr)]">
              <form
                onSubmit={onPackage}
                className="space-y-5 border border-[var(--line)] bg-[rgba(10,15,22,0.5)] p-5 md:p-6 animate-rise-delay"
              >
                <div>
                  <p className="ac-display text-xl text-[var(--gold-bright)]">Build delivery</p>
                  <p className="ac-serif mt-1 text-sm text-[var(--mist)]">
                    Select a cinema package to export 16:9 / 9:16 / 1:1 masters + stems.
                  </p>
                </div>

                {packages.length === 0 ? (
                  <EmptyState
                    title="No cinema package"
                    description="Render a cinematic advertising package before publishing."
                    action={
                      <Link href={`/cinema/${projectId}`} className="ac-btn ac-btn-primary">
                        Go to cinema
                      </Link>
                    }
                  />
                ) : (
                  <>
                    <div>
                      <label className="ac-label" htmlFor="pkg">
                        Cinema package
                      </label>
                      <select
                        id="pkg"
                        className="ac-field"
                        value={selectedPackage}
                        onChange={(e) => setSelectedPackage(e.target.value)}
                        required
                      >
                        {packages.map((pkg) => (
                          <option key={pkg.package_id} value={pkg.package_id}>
                            {pkg.campaign} · {pkg.duration_seconds}s
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="ac-label" htmlFor="channel">
                        Delivery channel
                      </label>
                      <select
                        id="channel"
                        className="ac-field"
                        value={channel}
                        onChange={(e) => setChannel(e.target.value)}
                      >
                        <option value="art_city_channel">Art City Channel</option>
                        <option value="youtube_16x9">YouTube 16:9</option>
                        <option value="social_vertical">Social vertical</option>
                        <option value="archive_master">Archive master</option>
                      </select>
                    </div>
                    <div>
                      <label className="ac-label" htmlFor="note">
                        Publisher note
                      </label>
                      <textarea
                        id="note"
                        className="ac-textarea min-h-[5rem]"
                        value={note}
                        onChange={(e) => setNote(e.target.value)}
                        placeholder="Final delivery for Kardokh pilot promo week…"
                      />
                    </div>
                    <button type="submit" disabled={busy} className="ac-btn ac-btn-primary">
                      {busy ? "Packaging…" : "Package masters"}
                    </button>
                  </>
                )}
              </form>

              <section className="animate-rise-late">
                <div className="mb-5 flex items-end justify-between gap-3">
                  <h2 className="ac-display text-lg">Publications</h2>
                  <span className="text-[0.68rem] tracking-[0.14em] text-[var(--mist-soft)] uppercase">
                    {publications.length} packaged
                  </span>
                </div>

                {publications.length === 0 ? (
                  <EmptyState
                    title="No publications yet"
                    description="Package a cinema campaign to generate the delivery checklist and masters."
                  />
                ) : (
                  <>
                    <ul className="mb-8 border-t border-[var(--line)]">
                      {publications.map((pub) => (
                        <li key={pub.publication_id}>
                          <button
                            type="button"
                            onClick={() => setActiveId(pub.publication_id)}
                            className={`ac-row w-full py-4 text-left ${
                              active?.publication_id === pub.publication_id
                                ? "bg-[rgba(197,161,94,0.06)]"
                                : ""
                            }`}
                          >
                            <p className="ac-display text-lg">{pub.campaign}</p>
                            <p className={`mt-1 text-[0.68rem] tracking-[0.12em] uppercase ${statusTone(pub.status ?? "")}`}>
                              {pub.status} · {pub.progress}% · {pub.channel}
                            </p>
                          </button>
                          <div className="ac-rule" />
                        </li>
                      ))}
                    </ul>

                    {active ? (
                      <div className="space-y-8">
                        <div className="border border-[var(--line)] p-5">
                          <div className="flex flex-wrap items-end justify-between gap-4">
                            <div>
                              <p className="ac-display text-2xl text-[var(--gold-bright)]">
                                {active.campaign}
                              </p>
                              <p className={`mt-2 text-[0.75rem] tracking-[0.16em] uppercase ${statusTone(active.status ?? "")}`}>
                                {active.status} · progress {active.progress}%
                              </p>
                            </div>
                            <div className="flex flex-wrap gap-2">
                              {active.manifest_url ? (
                                <a
                                  href={withAccessToken(`${API_URL}${active.manifest_url}`)}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="ac-btn ac-btn-secondary"
                                >
                                  Manifest
                                </a>
                              ) : null}
                              {active.report_url ? (
                                <a
                                  href={withAccessToken(`${API_URL}${active.report_url}`)}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="ac-btn ac-btn-ghost"
                                >
                                  Report
                                </a>
                              ) : null}
                              {active.status === "ready" ? (
                                <button
                                  type="button"
                                  disabled={busy}
                                  onClick={() => void onRelease()}
                                  className="ac-btn ac-btn-primary"
                                >
                                  {busy ? "Releasing…" : "Release to channel"}
                                </button>
                              ) : null}
                            </div>
                          </div>

                          <div className="mt-5 h-1.5 w-full bg-[rgba(255,255,255,0.06)]">
                            <div
                              className="h-full bg-gradient-to-r from-[var(--gold-deep)] to-[var(--gold-bright)] transition-all"
                              style={{ width: `${active.progress}%` }}
                            />
                          </div>
                        </div>

                        <div>
                          <h3 className="ac-display mb-4 text-[var(--paper)]">Delivery checklist</h3>
                          <ul className="space-y-0 border-t border-[var(--line)]">
                            {active.checklist.map((item) => (
                              <li key={item.id} className="border-b border-[var(--line)] py-3">
                                <div className="flex items-start justify-between gap-4">
                                  <div>
                                    <p className="text-[var(--paper)]">{item.label}</p>
                                    {item.detail ? (
                                      <p className="mt-1 text-xs text-[var(--mist-soft)]">{item.detail}</p>
                                    ) : null}
                                  </div>
                                  <span
                                    className={`ac-display shrink-0 text-[0.65rem] tracking-[0.14em] uppercase ${statusTone(item.status)}`}
                                  >
                                    {item.status}
                                  </span>
                                </div>
                              </li>
                            ))}
                          </ul>
                        </div>

                        <div>
                          <h3 className="ac-display mb-4 text-[var(--paper)]">Exported masters</h3>
                          <div className="grid gap-4">
                            {active.masters.map((m) => (
                              <MasterCard key={`${m.role}-${m.filename}`} master={m} />
                            ))}
                          </div>
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
