"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { CoreShell } from "@/components/CoreShell";
import { useLocale } from "@/components/LocaleProvider";
import {
  hubApi,
  type HubElement,
  type HubScene,
  type HubScript,
  type HubScriptVersion,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth";

const ELEMENT_TYPES = [
  "scene_heading",
  "action",
  "character",
  "parenthetical",
  "dialogue",
  "transition",
  "shot",
] as const;

type DraftElement = {
  key: string;
  element_type: string;
  display_text: string;
  locale?: string | null;
  id?: string;
};

export default function HubScriptPage() {
  const params = useParams<{ projectId: string }>();
  const projectId = params.projectId;
  const { t, locale } = useLocale();

  const [scripts, setScripts] = useState<HubScript[]>([]);
  const [script, setScript] = useState<HubScript | null>(null);
  const [version, setVersion] = useState<HubScriptVersion | null>(null);
  const [versions, setVersions] = useState<HubScriptVersion[]>([]);
  const [elements, setElements] = useState<DraftElement[]>([]);
  const [scenes, setScenes] = useState<HubScene[]>([]);
  const [title, setTitle] = useState("Untitled Screenplay");
  const [seed, setSeed] = useState("");
  const [status, setStatus] = useState("");
  const [saving, setSaving] = useState(false);
  const [stale, setStale] = useState<string[]>([]);

  const locked = version?.status === "locked";

  const loadScripts = useCallback(async () => {
    const list = await hubApi.listScripts(projectId);
    setScripts(list);
    if (list[0]) {
      const s = list[0];
      setScript(s);
      const vs = await hubApi.listVersions(s.id);
      setVersions(vs);
      const current = vs.find((v) => v.id === s.current_version_id) || vs[0];
      if (current) {
        setVersion(current);
        const els = await hubApi.listElements(current.id);
        setElements(
          els.map((e) => ({
            key: e.id,
            id: e.id,
            element_type: e.element_type,
            display_text: e.display_text,
            locale: e.locale,
          })),
        );
        const sc = await hubApi.listScenes(current.id).catch(() => [] as HubScene[]);
        setScenes(sc);
      }
      const flags = await hubApi.listStale(projectId).catch(() => []);
      setStale(flags.map((f) => f.reason));
    }
  }, [projectId]);

  async function openScript(s: HubScript) {
    setScript(s);
    const vs = await hubApi.listVersions(s.id);
    setVersions(vs);
    const current = vs.find((v) => v.id === s.current_version_id) || vs[0];
    if (current) await openVersion(current);
    const flags = await hubApi.listStale(projectId).catch(() => []);
    setStale(flags.map((f) => f.reason));
  }

  async function openVersion(v: HubScriptVersion) {
    setVersion(v);
    const els = await hubApi.listElements(v.id);
    setElements(
      els.map((e) => ({
        key: e.id,
        id: e.id,
        element_type: e.element_type,
        display_text: e.display_text,
        locale: e.locale,
      })),
    );
    const sc = await hubApi.listScenes(v.id).catch(() => [] as HubScene[]);
    setScenes(sc);
  }

  useEffect(() => {
    loadScripts().catch((e) => setStatus(String(e.message || e)));
  }, [loadScripts]);

  const sceneNav = useMemo(
    () => scenes.map((s) => ({ id: s.id, label: `${s.scene_number}. ${s.heading_display || s.location_name || ""}` })),
    [scenes],
  );

  async function createScript() {
    setStatus("Creating…");
    const s = await hubApi.createScript(projectId, {
      title,
      entry_mode: seed ? "synopsis" : "blank",
      primary_locale: locale === "ckb-IQ" ? "ckb-IQ" : "en",
      content_languages: locale === "ckb-IQ" ? ["ckb-IQ", "en"] : ["en"],
      seed_text: seed || undefined,
    });
    setStatus("Created");
    await openScript(s);
    await loadScripts();
  }

  async function save() {
    if (!version || locked) return;
    setSaving(true);
    try {
      const saved = await hubApi.saveElements(
        version.id,
        elements.map((e) => ({
          element_type: e.element_type,
          display_text: e.display_text,
          locale: e.locale || undefined,
        })),
      );
      setElements(
        saved.map((e: HubElement) => ({
          key: e.id,
          id: e.id,
          element_type: e.element_type,
          display_text: e.display_text,
          locale: e.locale,
        })),
      );
      setStatus(t("script.save") + " ✓");
    } catch (e) {
      setStatus(String((e as Error).message || e));
    } finally {
      setSaving(false);
    }
  }

  async function parseScenes() {
    if (!version || locked) return;
    await save();
    const sc = await hubApi.parseScenes(version.id);
    setScenes(sc);
    setStatus(`${t("script.parseScenes")}: ${sc.length}`);
  }

  async function lockVersion() {
    if (!version) return;
    const v = await hubApi.lockVersion(version.id);
    setVersion(v);
    setStatus(t("script.lock") + " ✓");
  }

  async function newRevision() {
    if (!script) return;
    const v = await hubApi.newRevision(script.id);
    setVersions((prev) => [v, ...prev]);
    await openVersion(v);
    setStatus(t("script.newDraft") + " ✓");
  }

  async function runAi(command: string, apply = false) {
    if (!version || locked) return;
    const res = await hubApi.aiCommand(version.id, {
      command,
      target_locale: locale === "ckb-IQ" ? "ckb-IQ" : "en",
      apply,
    });
    if (apply && res.elements?.length) {
      setElements(
        res.elements.map((e, i) => ({
          key: `ai-${i}`,
          element_type: e.element_type || "action",
          display_text: e.display_text || "",
          locale: (e as { locale?: string }).locale,
        })),
      );
    }
    setStatus(`AI ${command} via ${res.provider}`);
  }

  async function exportFile(fmt: "pdf" | "docx") {
    if (!version) return;
    const token = getAccessToken();
    const res = await fetch(hubApi.exportUrl(version.id, fmt), {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new Error(`Export failed ${res.status}`);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `screenplay.${fmt}`;
    a.click();
    URL.revokeObjectURL(url);
  }

  async function handoff(target: "cinema" | "studio" | "edit") {
    const res = await hubApi.handoff(projectId, target, {
      script_version_id: version?.id,
    });
    setStatus(`Handoff ${target} ✓`);
    if (res.redirect) window.location.href = res.redirect;
  }

  function updateElement(index: number, patch: Partial<DraftElement>) {
    setElements((prev) => prev.map((e, i) => (i === index ? { ...e, ...patch } : e)));
  }

  function addElement(after = elements.length - 1) {
    const next = [...elements];
    next.splice(after + 1, 0, {
      key: `new-${Date.now()}`,
      element_type: "action",
      display_text: "",
      locale: locale === "ckb-IQ" ? "ckb-IQ" : "en",
    });
    setElements(next);
  }

  function removeElement(index: number) {
    setElements((prev) => prev.filter((_, i) => i !== index));
  }

  return (
    <CoreShell title={t("hub.script")} subtitle={script?.title || projectId}>
      {stale.length ? (
        <div className="mb-4 border border-[var(--danger)] px-3 py-2 text-sm text-[var(--danger)]">
          {stale[0] || t("stale.scriptChanged")}
        </div>
      ) : null}

      <div className="mb-6 flex flex-wrap gap-2">
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="min-w-[12rem] flex-1 border border-[var(--line)] bg-transparent px-3 py-2"
          placeholder={t("hub.newScript")}
        />
        <button
          type="button"
          onClick={() => createScript().catch((e) => setStatus(String(e.message || e)))}
          className="border border-[var(--gold)] px-3 py-2 text-[0.7rem] uppercase tracking-[0.12em] text-[var(--gold-bright)]"
        >
          {t("hub.newScript")}
        </button>
        <Link
          href={`/hub/${projectId}/breakdown`}
          className="border border-[var(--line)] px-3 py-2 text-[0.7rem] uppercase tracking-[0.12em]"
        >
          {t("hub.breakdown")}
        </Link>
        <Link
          href={`/hub/${projectId}/script/versions`}
          className="border border-[var(--line)] px-3 py-2 text-[0.7rem] uppercase tracking-[0.12em]"
        >
          {t("script.compare")}
        </Link>
      </div>

      <textarea
        value={seed}
        onChange={(e) => setSeed(e.target.value)}
        rows={2}
        placeholder="Optional seed: idea / logline / synopsis / pasted screenplay…"
        className="mb-4 w-full border border-[var(--line)] bg-transparent px-3 py-2 text-sm"
        dir="auto"
      />

      {scripts.length > 1 ? (
        <div className="mb-4 flex flex-wrap gap-2">
          {scripts.map((s) => (
            <button
              key={s.id}
              type="button"
              onClick={() => openScript(s)}
              className={`border px-2 py-1 text-[0.7rem] ${
                script?.id === s.id ? "border-[var(--gold)] text-[var(--gold-bright)]" : "border-[var(--line)]"
              }`}
            >
              {s.title}
            </button>
          ))}
        </div>
      ) : null}

      {version ? (
        <div className="mb-4 flex flex-wrap items-center gap-2 text-[0.75rem] text-[var(--mist)]">
          <span>
            {version.version_label} · {version.status} · {version.page_eighths}/8 pages
          </span>
          <select
            value={version.id}
            onChange={(e) => {
              const v = versions.find((x) => x.id === e.target.value);
              if (v) openVersion(v);
            }}
            className="border border-[var(--line)] bg-transparent px-2 py-1"
          >
            {versions.map((v) => (
              <option key={v.id} value={v.id}>
                {v.version_label} ({v.status})
              </option>
            ))}
          </select>
          {locked ? <span className="text-[var(--danger)]">{t("script.locked")}</span> : null}
        </div>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-[14rem_1fr]">
        <aside className="border border-[var(--line)] p-3">
          <p className="mb-2 text-[0.65rem] uppercase tracking-[0.14em] text-[var(--mist)]">{t("scene.sceneNumber")}</p>
          <ul className="space-y-1 text-sm">
            {sceneNav.map((s) => (
              <li key={s.id} className="truncate text-[var(--paper-dim)]" title={s.label}>
                {s.label}
              </li>
            ))}
            {!sceneNav.length ? <li className="text-[var(--mist)]">—</li> : null}
          </ul>
        </aside>

        <div className="space-y-2">
          {elements.map((el, index) => (
            <div key={el.key} className="border border-[var(--line)] p-2">
              <div className="mb-1 flex flex-wrap gap-2">
                <select
                  disabled={locked}
                  value={el.element_type}
                  onChange={(e) => updateElement(index, { element_type: e.target.value })}
                  className="border border-[var(--line)] bg-transparent px-2 py-1 text-[0.7rem]"
                >
                  {ELEMENT_TYPES.map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  disabled={locked}
                  onClick={() => addElement(index)}
                  className="text-[0.65rem] uppercase text-[var(--mist)]"
                >
                  +
                </button>
                <button
                  type="button"
                  disabled={locked}
                  onClick={() => removeElement(index)}
                  className="text-[0.65rem] uppercase text-[var(--danger)]"
                >
                  ×
                </button>
              </div>
              <textarea
                disabled={locked}
                dir={el.element_type === "scene_heading" ? "ltr" : "auto"}
                value={el.display_text}
                onChange={(e) => updateElement(index, { display_text: e.target.value })}
                rows={el.element_type === "action" || el.element_type === "dialogue" ? 3 : 2}
                className={`w-full bg-transparent px-2 py-1 text-sm outline-none ${
                  el.element_type === "character" ? "text-center uppercase tracking-[0.08em]" : ""
                } ${el.element_type === "scene_heading" ? "font-semibold uppercase" : ""}`}
              />
            </div>
          ))}
          {!elements.length ? (
            <p className="text-[var(--mist)]">Create a script to start editing structured screenplay elements.</p>
          ) : null}
        </div>
      </div>

      <div className="mt-6 flex flex-wrap gap-2">
        <button
          type="button"
          disabled={!version || locked || saving}
          onClick={() => save().catch((e) => setStatus(String(e.message || e)))}
          className="border border-[var(--gold)] px-3 py-2 text-[0.7rem] uppercase tracking-[0.12em] text-[var(--gold-bright)] disabled:opacity-40"
        >
          {t("script.save")}
        </button>
        <button
          type="button"
          disabled={!version || locked}
          onClick={() => parseScenes().catch((e) => setStatus(String(e.message || e)))}
          className="border border-[var(--line)] px-3 py-2 text-[0.7rem] uppercase tracking-[0.12em]"
        >
          {t("script.parseScenes")}
        </button>
        <button
          type="button"
          disabled={!version || locked}
          onClick={() => lockVersion().catch((e) => setStatus(String(e.message || e)))}
          className="border border-[var(--line)] px-3 py-2 text-[0.7rem] uppercase tracking-[0.12em]"
        >
          {t("script.lock")}
        </button>
        <button
          type="button"
          disabled={!script}
          onClick={() => newRevision().catch((e) => setStatus(String(e.message || e)))}
          className="border border-[var(--line)] px-3 py-2 text-[0.7rem] uppercase tracking-[0.12em]"
        >
          {t("script.newDraft")}
        </button>
        <button
          type="button"
          disabled={!version || locked}
          onClick={() => runAi("polish", true).catch((e) => setStatus(String(e.message || e)))}
          className="border border-[var(--line)] px-3 py-2 text-[0.7rem] uppercase tracking-[0.12em]"
        >
          {t("script.aiPolish")}
        </button>
        <button
          type="button"
          disabled={!version || locked}
          onClick={() => runAi("translate", true).catch((e) => setStatus(String(e.message || e)))}
          className="border border-[var(--line)] px-3 py-2 text-[0.7rem] uppercase tracking-[0.12em]"
        >
          {t("script.aiTranslate")}
        </button>
        <button
          type="button"
          disabled={!version}
          onClick={() => exportFile("docx").catch((e) => setStatus(String(e.message || e)))}
          className="border border-[var(--line)] px-3 py-2 text-[0.7rem] uppercase tracking-[0.12em]"
        >
          {t("script.exportDocx")}
        </button>
        <button
          type="button"
          disabled={!version}
          onClick={() => exportFile("pdf").catch((e) => setStatus(String(e.message || e)))}
          className="border border-[var(--line)] px-3 py-2 text-[0.7rem] uppercase tracking-[0.12em]"
        >
          {t("script.exportPdf")}
        </button>
        <button
          type="button"
          disabled={!version}
          onClick={() => handoff("cinema").catch((e) => setStatus(String(e.message || e)))}
          className="border border-[var(--teal)] px-3 py-2 text-[0.7rem] uppercase tracking-[0.12em] text-[var(--teal)]"
        >
          {t("action.handoffCinema")}
        </button>
        <button
          type="button"
          disabled={!version}
          onClick={() => handoff("studio").catch((e) => setStatus(String(e.message || e)))}
          className="border border-[var(--teal)] px-3 py-2 text-[0.7rem] uppercase tracking-[0.12em] text-[var(--teal)]"
        >
          {t("action.handoffStudio")}
        </button>
        <button
          type="button"
          disabled={!version}
          onClick={() => handoff("edit").catch((e) => setStatus(String(e.message || e)))}
          className="border border-[var(--teal)] px-3 py-2 text-[0.7rem] uppercase tracking-[0.12em] text-[var(--teal)]"
        >
          {t("action.handoffEdit")}
        </button>
      </div>
      {status ? <p className="mt-3 text-sm text-[var(--mist)]">{status}</p> : null}
    </CoreShell>
  );
}
