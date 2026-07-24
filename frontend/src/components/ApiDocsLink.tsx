"use client";

const API_DOCS =
  process.env.NEXT_PUBLIC_API_DOCS_URL ??
  "https://backend-production-9533.up.railway.app/docs";

/** Active header control — opens live Art City OpenAPI / Swagger docs. */
export function ApiDocsLink() {
  return (
    <a
      href={API_DOCS}
      target="_blank"
      rel="noreferrer"
      title="Art City API documentation"
      aria-label="API documentation"
      className="group flex items-center gap-2 rounded-[var(--radius)] border border-[var(--gold)] bg-[rgba(197,161,94,0.14)] px-3 py-1.5 text-[0.68rem] uppercase tracking-[0.16em] text-[var(--gold-bright)] transition hover:bg-[rgba(197,161,94,0.28)]"
    >
      <span className="relative flex h-4 w-4 items-center justify-center" aria-hidden>
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[var(--gold)] opacity-30" />
        <svg
          viewBox="0 0 24 24"
          className="relative h-3.5 w-3.5 fill-none stroke-current stroke-[1.75]"
        >
          <path d="M7 7h10v10H7z" />
          <path d="M9 10h6M9 12.5h4M9 15h5" strokeLinecap="square" />
        </svg>
      </span>
      <span className="hidden sm:inline">API docs</span>
    </a>
  );
}
