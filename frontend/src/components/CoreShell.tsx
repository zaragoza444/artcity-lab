"use client";

import { SiteHeader } from "@/components/SiteHeader";
import { PageHeader } from "@/components/PageHeader";

export function CoreShell({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}) {
  return (
    <>
      <SiteHeader />
      <main className="ac-container py-10">
        <PageHeader title={title} description={subtitle} eyebrow="Art City AI Core" />
        <div className="mt-8">{children}</div>
      </main>
    </>
  );
}
