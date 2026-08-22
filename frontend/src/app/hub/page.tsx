"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { CoreShell } from "@/components/CoreShell";
import { useLocale } from "@/components/LocaleProvider";
import { api, hubApi, type HubFeatures, type Project } from "@/lib/api";

export default function HubHomePage() {
  const { t } = useLocale();
  const [projects, setProjects] = useState<Project[]>([]);
  const [features, setFeatures] = useState<HubFeatures | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api.listProjects(), hubApi.features()])
      .then(([p, f]) => {
        setProjects(p);
        setFeatures(f);
      })
      .catch((e) => setError(String(e.message || e)));
  }, []);

  const modules = [
    {
      key: "script",
      title: t("hub.script"),
      enabled: features?.script ?? true,
      href: (id: string) => `/hub/${id}/script`,
    },
    {
      key: "storyboard",
      title: t("hub.storyboard"),
      enabled: features?.storyboard ?? false,
      href: () => "#",
    },
    {
      key: "budget",
      title: t("hub.budget"),
      enabled: features?.budget ?? false,
      href: () => "#",
    },
    {
      key: "call",
      title: t("hub.call"),
      enabled: features?.call ?? false,
      href: () => "#",
    },
  ];

  return (
    <CoreShell title={t("hub.title")} subtitle={t("hub.subtitle")}>
      {error ? <p className="text-[var(--danger)]">{error}</p> : null}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {modules.map((m) => (
          <div key={m.key} className="border border-[var(--line)] px-4 py-5">
            <p className="text-sm uppercase tracking-[0.14em] text-[var(--gold-bright)]">{m.title}</p>
            <p className="mt-2 text-[0.8rem] text-[var(--mist)]">
              {m.enabled ? t("hub.openScript") : t("hub.comingSoon")}
            </p>
          </div>
        ))}
      </div>
      <h2 className="mt-10 text-sm uppercase tracking-[0.16em] text-[var(--mist)]">{t("project.title")}</h2>
      <div className="mt-4 grid gap-3">
        {projects.map((p) => (
          <div
            key={p.id}
            className="flex flex-wrap items-center justify-between gap-3 border border-[var(--line)] px-4 py-4"
          >
            <div>
              <p className="text-[var(--paper)]">{p.name}</p>
              <p className="text-[0.75rem] text-[var(--mist)]">{p.id}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Link
                href={`/hub/${p.id}/script`}
                className="border border-[var(--gold)] px-3 py-1.5 text-[0.7rem] uppercase tracking-[0.12em] text-[var(--gold-bright)]"
              >
                {t("hub.script")}
              </Link>
              <Link
                href={`/hub/${p.id}/breakdown`}
                className="border border-[var(--line)] px-3 py-1.5 text-[0.7rem] uppercase tracking-[0.12em] text-[var(--mist)]"
              >
                {t("hub.breakdown")}
              </Link>
              <Link
                href={`/cinema/${p.id}`}
                className="border border-[var(--line)] px-3 py-1.5 text-[0.7rem] uppercase tracking-[0.12em] text-[var(--mist)]"
              >
                Cinema
              </Link>
              <Link
                href={`/studio/${p.id}`}
                className="border border-[var(--line)] px-3 py-1.5 text-[0.7rem] uppercase tracking-[0.12em] text-[var(--mist)]"
              >
                Studio
              </Link>
            </div>
          </div>
        ))}
        {!projects.length ? (
          <p className="text-[var(--mist)]">
            No projects yet. Create one under{" "}
            <Link href="/projects" className="text-[var(--gold-bright)]">
              Projects
            </Link>
            .
          </p>
        ) : null}
      </div>
    </CoreShell>
  );
}
