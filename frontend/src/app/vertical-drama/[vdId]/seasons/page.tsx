"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { CoreShell } from "@/components/CoreShell";
import { VdNav } from "@/components/VdNav";
import { vdApi, type VdProject } from "@/lib/api";

type Episode = {
  id: string;
  episode_number: number;
  title: string;
  hook?: string;
  cliffhanger?: string;
  status: string;
  stale?: boolean;
};

export default function SeasonsPage() {
  const { vdId } = useParams<{ vdId: string }>();
  const [p, setP] = useState<VdProject | null>(null);
  const [seasons, setSeasons] = useState<{ id: string; title: string; episodes: Episode[] }[]>([]);
  const [count, setCount] = useState(10);

  async function load() {
    setP(await vdApi.get(vdId));
    setSeasons((await vdApi.seasons(vdId)) as { id: string; title: string; episodes: Episode[] }[]);
  }
  useEffect(() => {
    load().catch(() => undefined);
  }, [vdId]);

  return (
    <CoreShell title="Season board" subtitle={p?.title || ""}>
      {p ? <VdNav vdId={p.id} projectId={p.project_id} /> : null}
      <div className="mb-4 flex gap-2">
        <input type="number" value={count} onChange={(e) => setCount(Number(e.target.value))} className="w-24 border border-[var(--line)] bg-transparent px-3 py-2" />
        <button type="button" onClick={() => vdApi.createSeason(vdId, { title: "Season 1", target_episode_count: count }).then(load)} className="border border-[var(--gold)] px-3 py-2 text-[0.7rem] uppercase text-[var(--gold-bright)]">
          Generate grid
        </button>
      </div>
      {seasons.map((s) => (
        <div key={s.id} className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="text-[0.65rem] uppercase text-[var(--mist)]">
                <th className="py-2">#</th>
                <th>Title</th>
                <th>Hook</th>
                <th>Cliffhanger</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {s.episodes.map((e) => (
                <tr key={e.id} className="border-t border-[var(--line)]">
                  <td className="py-2">{e.episode_number}</td>
                  <td>
                    <Link href={`/vertical-drama/${vdId}/episodes/${e.id}`} className="text-[var(--gold-bright)]">
                      {e.title}
                    </Link>
                    {e.stale ? <span className="ml-2 text-[var(--danger)]">stale</span> : null}
                  </td>
                  <td>{e.hook}</td>
                  <td>{e.cliffhanger}</td>
                  <td>{e.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </CoreShell>
  );
}
