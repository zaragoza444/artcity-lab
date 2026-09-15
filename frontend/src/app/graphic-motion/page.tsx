"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { CoreShell } from "@/components/CoreShell";
import { api, graphicMotionApi, type AgmScene, type Project } from "@/lib/api";

const SORANI_SEED = {
  schema_version: "1.0.0",
  name: "Sorani headline reveal",
  locale: "ckb-IQ",
  direction: "rtl" as const,
  canvas: {
    width: 1920,
    height: 1080,
    fps: 25,
    duration_ms: 8000,
    background: "#00000000",
    color_space: "rec709",
  },
  timeline: { timebase: "ms", play_start_ms: 0, play_end_ms: 8000 },
  brand_context: null,
  variables: {},
  nodes: [
    {
      id: "headline",
      type: "text",
      start_ms: 250,
      end_ms: 8000,
      z_index: 10,
      visible: true,
      transform: { x: 960, y: 540, opacity: 1 },
      payload: {
        text: "هەواڵی گرنگ",
        language: "ckb",
        direction: "rtl",
        unicode_bidi: "plaintext",
        font: { asset_id: "00000000-0000-4000-8000-0000000000aa", weight: 700 },
        font_size: 72,
        fill: "#FFFFFFFF",
        shaping_engine: "harfbuzz",
        normalization: "NFC",
        animation_unit: "word",
        align: "center",
        wrap: "word",
        overflow: "clip",
      },
      animations: [
        {
          property: "transform.opacity",
          keyframes: [
            { time_ms: 250, value: 0, easing: "ease-out" },
            { time_ms: 900, value: 1, easing: "linear" },
          ],
        },
      ],
      effects: [],
      bindings: [],
      tags: ["headline", "sorani"],
    },
  ],
  markers: [],
  audio: [],
  metadata: { demo: "ckb-reference" },
};

export default function GraphicMotionHomePage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selected, setSelected] = useState("");
  const [scenes, setScenes] = useState<AgmScene[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api
      .listProjects()
      .then((p) => {
        setProjects(p);
        if (p[0]) setSelected(p[0].id);
      })
      .catch((e) => setError(String(e.message || e)));
  }, []);

  useEffect(() => {
    if (!selected) return;
    graphicMotionApi
      .listScenes(selected)
      .then(setScenes)
      .catch((e) => setError(String(e.message || e)));
  }, [selected]);

  async function createSorani() {
    if (!selected) return;
    setBusy(true);
    setError("");
    try {
      const scene = await graphicMotionApi.createScene({
        project_id: selected,
        name: "Sorani headline reveal",
        locale: "ckb-IQ",
        direction: "rtl",
        graph: {
          ...SORANI_SEED,
          scene_id: "00000000-0000-4000-8000-000000000001",
          project_id: selected,
        },
      });
      setScenes((prev) => [scene, ...prev]);
    } catch (e) {
      setError(String((e as Error).message || e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <CoreShell
      title="Graphic Motion"
      subtitle="MSG scenes · Sorani/RTL · preview & broadcast render · Art City ACX"
    >
      {error ? <p className="text-[var(--danger)]">{error}</p> : null}
      <div className="flex flex-wrap items-end gap-3">
        <label className="block text-[0.7rem] uppercase tracking-[0.12em] text-[var(--mist)]">
          Project
          <select
            className="mt-1 block min-w-[14rem] border border-[var(--line)] bg-transparent px-3 py-2 text-[var(--paper)]"
            value={selected}
            onChange={(e) => setSelected(e.target.value)}
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </label>
        <button
          type="button"
          disabled={busy || !selected}
          onClick={createSorani}
          className="border border-[var(--gold)] px-4 py-2 text-[0.7rem] uppercase tracking-[0.12em] text-[var(--gold-bright)] disabled:opacity-40"
        >
          Create Sorani example
        </button>
      </div>
      <h2 className="mt-10 text-sm uppercase tracking-[0.16em] text-[var(--mist)]">Scenes</h2>
      <div className="mt-4 grid gap-3">
        {scenes.length === 0 ? (
          <p className="text-[var(--mist)]">No scenes yet for this project.</p>
        ) : (
          scenes.map((s) => (
            <Link
              key={s.id}
              href={`/graphic-motion/${s.id}`}
              className="flex flex-wrap items-center justify-between gap-3 border border-[var(--line)] px-4 py-4 hover:border-[var(--gold)]"
            >
              <div>
                <p className="text-[var(--paper)]" dir={s.direction === "rtl" ? "rtl" : "ltr"}>
                  {s.name}
                </p>
                <p className="text-[0.75rem] text-[var(--mist)]">
                  {s.locale} · rev {s.head_revision_id?.slice(0, 8) || "—"}
                </p>
              </div>
              <span className="text-[0.7rem] uppercase tracking-[0.12em] text-[var(--gold-bright)]">Open</span>
            </Link>
          ))
        )}
      </div>
    </CoreShell>
  );
}
