"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { SiteHeader } from "@/components/SiteHeader";
import { PageHeader } from "@/components/PageHeader";
import { useLocale } from "@/components/LocaleProvider";

const links = [
  ["", "comm.overview"],
  ["/contacts", "comm.contacts"],
  ["/segments", "comm.segments"],
  ["/imports", "comm.imports"],
  ["/templates", "comm.templates"],
  ["/campaigns", "comm.campaigns"],
  ["/inbox", "comm.inbox"],
  ["/billing", "comm.billing"],
  ["/admin", "comm.admin"],
] as const;

export function CommunicationsFrame({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const { t } = useLocale();
  return (
    <>
      <SiteHeader />
      <main className="ac-container py-10">
        <PageHeader eyebrow="AC Communications" title={title} description={t("comm.subtitle")} />
        <nav className="mb-8 flex gap-2 overflow-x-auto" aria-label="Communications">
          {links.map(([href, key]) => {
            const path = `/communications${href}`;
            const active = href === "" ? pathname === "/communications" : pathname.startsWith(path);
            return (
              <Link
                key={path}
                href={path}
                className={`whitespace-nowrap border px-3 py-1.5 text-[0.72rem] uppercase tracking-[0.12em] ${
                  active ? "border-[var(--gold)] text-[var(--gold-bright)]" : "border-[var(--line)] text-[var(--mist)]"
                }`}
              >
                {t(key)}
              </Link>
            );
          })}
        </nav>
        {children}
      </main>
    </>
  );
}

export function CommError({ error }: { error: string }) {
  if (!error) return null;
  return <p className="mb-4 text-sm text-red-300">{error}</p>;
}
