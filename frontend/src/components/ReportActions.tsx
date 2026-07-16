"use client";

export function ReportActions({
  pdfUrl,
  markdownUrl,
}: {
  pdfUrl: string;
  markdownUrl: string;
}) {
  return (
    <div className="flex flex-wrap gap-3">
      <a
        href={pdfUrl}
        download
        className="border border-[var(--gold)] bg-[rgba(197,161,94,0.12)] px-4 py-2 text-sm text-[var(--gold-bright)] transition hover:bg-[rgba(197,161,94,0.22)]"
      >
        Download PDF
      </a>
      <a
        href={markdownUrl}
        className="border border-[var(--line)] px-4 py-2 text-sm text-[var(--paper-dim)] transition hover:border-[var(--line-strong)] hover:text-[var(--paper)]"
      >
        Markdown
      </a>
      <button
        type="button"
        onClick={() => window.print()}
        className="border border-[var(--line)] px-4 py-2 text-sm text-[var(--paper-dim)] transition hover:border-[var(--line-strong)] hover:text-[var(--paper)] print:hidden"
      >
        Print / Save as PDF
      </button>
    </div>
  );
}
