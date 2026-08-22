"use client";

import Link from "next/link";

export function VdNav({ vdId, projectId }: { vdId: string; projectId: string }) {
  const base = `/vertical-drama/${vdId}`;
  const links = [
    ["Overview", `${base}`],
    ["IP Vault", `${base}/ip-vault`],
    ["World", `${base}/world`],
    ["Story Bible", `${base}/story-bible`],
    ["Season", `${base}/seasons`],
    ["Hub Script", `/hub/${projectId}/script`],
    ["Cinema", `/cinema/${projectId}`],
    ["Edit", `/edit`],
  ];
  return (
    <nav className="mb-6 flex flex-wrap gap-2">
      {links.map(([label, href]) => (
        <Link
          key={href}
          href={href}
          className="border border-[var(--line)] px-3 py-1.5 text-[0.7rem] uppercase tracking-[0.12em] text-[var(--mist)] hover:border-[var(--gold)] hover:text-[var(--gold-bright)]"
        >
          {label}
        </Link>
      ))}
    </nav>
  );
}
