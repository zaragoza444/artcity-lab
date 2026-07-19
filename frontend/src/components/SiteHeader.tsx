"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ApiDocsLink } from "@/components/ApiDocsLink";
import { ApiStatus } from "@/components/ApiStatus";
import { BrandMark } from "@/components/BrandMark";
import { useAuth } from "@/components/AuthProvider";

const primary = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/projects", label: "Projects" },
  { href: "/cinema", label: "Cinema" },
  { href: "/studio", label: "Studio" },
  { href: "/publish", label: "Publish" },
];

const core = [
  { href: "/data-lab", label: "Data Lab" },
  { href: "/knowledge", label: "Knowledge" },
  { href: "/speech", label: "Speech" },
  { href: "/rights", label: "Rights" },
  { href: "/models", label: "Models" },
  { href: "/training", label: "Training" },
  { href: "/evaluations", label: "Evaluations" },
  { href: "/costs", label: "Costs" },
  { href: "/users", label: "Users" },
  { href: "/settings", label: "Settings" },
];

export function SiteHeader({ transparent = false }: { transparent?: boolean }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const product =
    pathname.startsWith("/cinema")
      ? "cinema"
      : pathname.startsWith("/studio")
        ? "studio"
        : "platform";

  return (
    <header
      className={`sticky top-0 z-20 border-b ${
        transparent
          ? "border-transparent bg-transparent"
          : "border-[var(--line)] bg-[rgba(5,7,11,0.72)] backdrop-blur-md"
      }`}
    >
      <div className="ac-container flex min-h-[var(--header-h)] flex-col justify-center gap-2 py-2">
        <div className="flex items-center justify-between gap-6">
          <div className="flex min-w-0 items-center gap-8">
            <BrandMark product={product} />
            <nav className="hidden items-center gap-1 lg:flex" aria-label="Primary">
              {primary.map((link) => {
                const active =
                  pathname === link.href || pathname.startsWith(`${link.href}/`);
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={`relative px-2.5 py-2 text-[0.72rem] uppercase tracking-[0.12em] transition ${
                      active
                        ? "text-[var(--gold-bright)]"
                        : "text-[var(--mist)] hover:text-[var(--paper)]"
                    }`}
                  >
                    {link.label}
                  </Link>
                );
              })}
            </nav>
          </div>
          <div className="flex items-center gap-3">
            {user ? (
              <button
                type="button"
                onClick={logout}
                className="hidden text-[0.7rem] uppercase tracking-[0.12em] text-[var(--mist)] hover:text-[var(--paper)] sm:inline"
              >
                {user.full_name.split(" ")[0]} · Sign out
              </button>
            ) : null}
            <ApiDocsLink />
            <ApiStatus />
          </div>
        </div>
        <nav
          className="hidden gap-1 overflow-x-auto pb-1 md:flex"
          aria-label="AI Core"
        >
          {core.map((link) => {
            const active = pathname === link.href || pathname.startsWith(`${link.href}/`);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`whitespace-nowrap px-2 py-1 text-[0.65rem] uppercase tracking-[0.14em] ${
                  active ? "text-[var(--teal)]" : "text-[var(--mist-soft)] hover:text-[var(--mist)]"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
