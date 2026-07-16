"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ApiStatus } from "@/components/ApiStatus";
import { BrandMark } from "@/components/BrandMark";

const links = [
  { href: "/", label: "Home" },
  { href: "/cinema", label: "Cinema" },
  { href: "/studio", label: "Studio" },
  { href: "/publish", label: "Publish" },
  { href: "/projects", label: "Projects" },
];

export function SiteHeader({ transparent = false }: { transparent?: boolean }) {
  const pathname = usePathname();
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
      <div className="ac-container flex h-[var(--header-h)] items-center justify-between gap-6">
        <div className="flex items-center gap-10 min-w-0">
          <BrandMark product={product} />
          <nav className="hidden sm:flex items-center gap-1" aria-label="Primary">
            {links.map((link) => {
              const active =
                link.href === "/"
                  ? pathname === "/"
                  : pathname === link.href || pathname.startsWith(`${link.href}/`);
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`relative px-3 py-2 text-[0.78rem] tracking-[0.14em] uppercase transition ${
                    active
                      ? "text-[var(--gold-bright)]"
                      : "text-[var(--mist)] hover:text-[var(--paper)]"
                  }`}
                >
                  {link.label}
                  {active ? (
                    <span className="absolute inset-x-3 -bottom-[1px] h-px bg-[var(--gold)]" />
                  ) : null}
                </Link>
              );
            })}
          </nav>
        </div>
        <ApiStatus />
      </div>
    </header>
  );
}
