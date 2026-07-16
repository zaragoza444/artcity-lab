import Link from "next/link";
import { SiteHeader } from "@/components/SiteHeader";

const API_DOCS =
  process.env.NEXT_PUBLIC_API_DOCS_URL ?? "http://localhost:8000/docs";

export default function HomePage() {
  return (
    <main className="relative flex min-h-screen flex-col overflow-hidden">
      <div className="ac-hero-plane" aria-hidden>
        <div className="ac-hero-beam" />
        <div className="ac-hero-horizon" />
      </div>

      <SiteHeader transparent />

      <section className="ac-container relative flex flex-1 flex-col justify-center py-16 md:py-24">
        <div className="max-w-3xl">
          <p className="ac-display mb-6 text-[0.7rem] tracking-[0.42em] text-[var(--mist)] uppercase animate-fade">
            Art City · Owned production platform
          </p>
          <h1 className="ac-display animate-rise">
            <span className="block text-[clamp(3.2rem,9vw,6rem)] leading-[0.9] tracking-[-0.03em] text-[var(--paper)]">
              Art City
            </span>
            <span className="ac-brand-sheen mt-3 block text-[clamp(2.4rem,7vw,4.2rem)] leading-[0.95] tracking-[-0.03em]">
              Cinema &amp; Studio
            </span>
          </h1>
          <p className="ac-serif mt-8 max-w-xl text-[1.12rem] leading-[1.75] text-[var(--paper-dim)] animate-rise-delay">
            Two products. One ownership model. Cinema builds complete advertising campaigns.
            Studio crafts individual production assets.
          </p>
        </div>

        <div className="mt-12 grid gap-5 md:grid-cols-2 animate-rise-late">
          <Link
            href="/cinema"
            className="group border border-[var(--line)] bg-[rgba(10,15,22,0.55)] p-6 transition hover:border-[var(--gold)]"
          >
            <p className="ac-display text-[0.68rem] tracking-[0.28em] text-[var(--gold-bright)] uppercase">
              Art City Cinema
            </p>
            <p className="ac-display mt-3 text-2xl text-[var(--paper)]">
              Complete advertising campaigns
            </p>
            <ul className="ac-serif mt-4 space-y-1 text-sm text-[var(--mist)]">
              <li>Hero film · Social adaptations</li>
              <li>Music · Voice-over · End card</li>
              <li>Campaign manifest · Technical QC · ZIP</li>
            </ul>
            <span className="mt-5 inline-block text-sm text-[var(--gold-bright)] transition group-hover:translate-x-1">
              Enter Cinema →
            </span>
          </Link>

          <Link
            href="/studio"
            className="group border border-[var(--line)] bg-[rgba(10,15,22,0.55)] p-6 transition hover:border-[var(--teal)]"
          >
            <p className="ac-display text-[0.68rem] tracking-[0.28em] text-[var(--teal)] uppercase">
              Art City Studio
            </p>
            <p className="ac-display mt-3 text-2xl text-[var(--paper)]">
              Individual production assets
            </p>
            <ul className="ac-serif mt-4 space-y-1 text-sm text-[var(--mist)]">
              <li>Single image · Single video</li>
              <li>Single voice · Single music</li>
              <li>Scene / shot takes · Review bay</li>
            </ul>
            <span className="mt-5 inline-block text-sm text-[var(--teal)] transition group-hover:translate-x-1">
              Enter Studio →
            </span>
          </Link>
        </div>

        <div className="mt-8 flex flex-wrap gap-3">
          <Link href="/publish" className="ac-btn ac-btn-primary">
            Publish masters
          </Link>
          <a href={API_DOCS} target="_blank" rel="noreferrer" className="ac-btn ac-btn-ghost">
            API docs
          </a>
        </div>
      </section>

      <footer className="ac-container relative border-t border-[var(--line)] py-7">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <p className="ac-display text-[0.68rem] tracking-[0.22em] text-[var(--mist)] uppercase">
            Art City proprietary platform
          </p>
          <p className="text-[0.8rem] tracking-[0.08em] text-[var(--mist-soft)] uppercase">
            Art City ownership · Cinema + Studio
          </p>
        </div>
      </footer>
    </main>
  );
}
