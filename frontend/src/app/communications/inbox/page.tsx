"use client";

import { useEffect, useState } from "react";
import { CommError, CommunicationsFrame } from "@/components/CommunicationsFrame";
import { useLocale } from "@/components/LocaleProvider";
import { commRequest } from "@/lib/communications";

type Conversation = {
  id: string;
  state: string;
  window_open: boolean;
  unread_count: number;
  service_window_expires_at: string | null;
  messages?: { id: string; direction: string; text: string | null; status: string }[];
};

export default function InboxPage() {
  const { t } = useLocale();
  const [rows, setRows] = useState<Conversation[]>([]);
  const [open, setOpen] = useState<Conversation | null>(null);
  const [text, setText] = useState("");
  const [error, setError] = useState("");

  async function load() {
    setRows(await commRequest<Conversation[]>("/inbox/conversations"));
  }

  useEffect(() => {
    load().catch((err: Error) => setError(err.message));
  }, []);

  return (
    <CommunicationsFrame title={t("comm.inbox")}>
      <CommError error={error} />
      <ul className="mb-6 space-y-2">
        {rows.map((row) => (
          <li key={row.id}>
            <button
              className="w-full border border-[var(--line)] px-3 py-2 text-left text-sm"
              type="button"
              onClick={async () => {
                try {
                  setOpen(await commRequest<Conversation>(`/inbox/conversations/${row.id}`));
                } catch (err) {
                  setError(err instanceof Error ? err.message : "Could not open conversation");
                }
              }}
            >
              {row.state} · unread {row.unread_count} · window {row.window_open ? "open" : "closed"}
            </button>
          </li>
        ))}
      </ul>
      {open ? (
        <section className="border border-[var(--line)] p-4">
          <p className="mb-2 text-sm">Service window {open.window_open ? "open until " + open.service_window_expires_at : "closed — a free-form reply is blocked"}</p>
          <ul className="mb-3 space-y-1 text-sm">
            {(open.messages || []).map((message) => (
              <li key={message.id} dir="auto">{message.direction}: {message.text}</li>
            ))}
          </ul>
          <form
            className="flex gap-2"
            onSubmit={async (event) => {
              event.preventDefault();
              try {
                await commRequest(`/inbox/conversations/${open.id}/reply`, { method: "POST", body: JSON.stringify({ text }) });
                setText("");
                setOpen(await commRequest<Conversation>(`/inbox/conversations/${open.id}`));
              } catch (err) {
                setError(err instanceof Error ? err.message : "Reply failed");
              }
            }}
          >
            <input className="ac-input flex-1" value={text} onChange={(e) => setText(e.target.value)} dir="auto" disabled={!open.window_open} />
            <button className="ac-btn ac-btn-primary" type="submit" disabled={!open.window_open}>Reply</button>
          </form>
        </section>
      ) : null}
    </CommunicationsFrame>
  );
}
