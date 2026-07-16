"use client";

import { useEffect, useState } from "react";
import { api, type Health } from "@/lib/api";

export function ApiStatus() {
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let alive = true;

    const load = () => {
      api
        .health()
        .then((h) => {
          if (!alive) return;
          setHealth(h);
          setError(false);
        })
        .catch(() => {
          if (!alive) return;
          setError(true);
          setHealth(null);
        });
    };

    load();
    const id = window.setInterval(load, 20000);
    return () => {
      alive = false;
      window.clearInterval(id);
    };
  }, []);

  const ok = health?.status === "ok";
  const label = error
    ? "Offline"
    : ok
      ? "Live"
      : health
        ? "Degraded"
        : "Syncing";

  return (
    <div
      className="flex items-center gap-2.5 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--ink-panel)] px-3.5 py-1.5 text-[0.68rem] tracking-[0.16em] uppercase text-[var(--mist)] backdrop-blur-sm"
      title={
        health
          ? `Database ${health.database} · Redis ${health.redis} · Storage ${health.minio}`
          : undefined
      }
    >
      <span
        className={`status-dot inline-block h-1.5 w-1.5 rounded-full ${
          error ? "bg-[var(--danger)]" : ok ? "bg-emerald-400" : "bg-[var(--gold)]"
        }`}
      />
      <span className="whitespace-nowrap">{label}</span>
    </div>
  );
}
