import fs from "fs";
import path from "path";
import Link from "next/link";
import { SiteHeader } from "@/components/SiteHeader";
import { ReportActions } from "@/components/ReportActions";
import { ReportMarkdown } from "@/components/ReportMarkdown";

export const metadata = {
  title: "Alltra Tokens, Funds & Liquidity Report",
  description:
    "Live research report on the Alltra blockchain ecosystem: tokens, funds, liquidity, and on-chain data.",
};

function getReportContent(): string {
  const reportPath = path.join(process.cwd(), "content", "alltra-report.md");
  return fs.readFileSync(reportPath, "utf8");
}

export default function AlltraReportPage() {
  const content = getReportContent();
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";
  const liveUrl = `${baseUrl}/reports/alltra`;
  const pdfUrl = `${baseUrl}/reports/alltra-report.pdf`;
  const htmlUrl = `${baseUrl}/reports/alltra-report.html`;
  const markdownUrl = `${baseUrl}/reports/alltra-report.md`;

  return (
    <main className="min-h-screen">
      <SiteHeader />

      <div className="ac-container py-10 md:py-14">
        <div className="mb-8 flex flex-col gap-4 border border-[var(--line)] bg-[rgba(10,15,22,0.55)] p-5 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="ac-display text-[0.68rem] tracking-[0.28em] text-[var(--gold-bright)] uppercase">
              Research report
            </p>
            <h1 className="ac-display mt-2 text-2xl text-[var(--paper)] md:text-3xl">
              Alltra Tokens, Funds &amp; Liquidity
            </h1>
            <p className="ac-serif mt-2 text-sm text-[var(--mist)]">
              Live page · PDF download · Markdown source
            </p>
          </div>
          <ReportActions pdfUrl={pdfUrl} markdownUrl={markdownUrl} />
        </div>

        <div className="mb-6 rounded border border-[var(--line)] bg-[rgba(5,7,11,0.45)] p-4 text-sm text-[var(--mist)]">
          <p>
            <span className="text-[var(--paper)]">Live link:</span>{" "}
            <a href={liveUrl} className="text-[var(--gold-bright)] underline">
              {liveUrl}
            </a>
          </p>
          <p className="mt-2">
            <span className="text-[var(--paper)]">PDF:</span>{" "}
            <a href={pdfUrl} className="text-[var(--gold-bright)] underline">
              {pdfUrl}
            </a>
          </p>
          <p className="mt-2">
            <span className="text-[var(--paper)]">HTML:</span>{" "}
            <a href={htmlUrl} className="text-[var(--gold-bright)] underline">
              {htmlUrl}
            </a>
          </p>
        </div>

        <article className="report-prose border border-[var(--line)] bg-[rgba(10,15,22,0.4)] p-6 md:p-10">
          <ReportMarkdown content={content} />
        </article>

        <p className="ac-serif mt-8 text-center text-sm text-[var(--mist)]">
          <Link href="/" className="text-[var(--gold-bright)] hover:underline">
            ← Back to Art City AI Studio
          </Link>
        </p>
      </div>
    </main>
  );
}
