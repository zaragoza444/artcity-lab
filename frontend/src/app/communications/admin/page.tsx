"use client";

import { useEffect, useState } from "react";
import { CommError, CommunicationsFrame } from "@/components/CommunicationsFrame";
import { useLocale } from "@/components/LocaleProvider";
import { commRequest } from "@/lib/communications";

type Provider = {
  provider_kind: string;
  live_send_enabled: boolean;
  token_configured: boolean;
  token: null;
  phone_number_id_configured: boolean;
  waba_configured: boolean;
  graph_api_version: string;
  coexistence_enabled: boolean;
};
type Member = { id: string; user_id: string; role: string; totp_enabled: boolean };

export default function AdminPage() {
  const { t } = useLocale();
  const [provider, setProvider] = useState<Provider | null>(null);
  const [members, setMembers] = useState<Member[]>([]);
  const [health, setHealth] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      commRequest<Provider>("/administration/provider"),
      commRequest<Member[]>("/administration/members"),
      commRequest<Record<string, string>>("/system/health"),
    ])
      .then(([providerRow, memberRows, healthRow]) => {
        setProvider(providerRow);
        setMembers(memberRows);
        setHealth(JSON.stringify(healthRow));
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  return (
    <CommunicationsFrame title={t("comm.admin")}>
      <CommError error={error} />
      {provider ? (
        <div className="space-y-2 text-sm">
          <p>Provider {provider.provider_kind} · Graph {provider.graph_api_version}</p>
          <p>Live send {provider.live_send_enabled ? "on" : "off"} · Token configured {provider.token_configured ? "yes" : "no"} · Token value hidden</p>
          <p>Phone number id {provider.phone_number_id_configured ? "set" : "missing"} · WABA {provider.waba_configured ? "set" : "missing"}</p>
          <p>Coexistence {provider.coexistence_enabled ? "on" : "not approved"}</p>
          <p>Health {health}</p>
        </div>
      ) : null}
      <ul className="mt-6 space-y-2 text-sm">
        {members.map((row) => (
          <li key={row.id} className="border border-[var(--line)] px-3 py-2">
            {row.role} · MFA {row.totp_enabled ? "on" : "off"}
          </li>
        ))}
      </ul>
      <button
        className="ac-btn mt-4"
        type="button"
        onClick={async () => {
          try {
            const enrolled = await commRequest<{ otpauth_uri: string }>("/administration/mfa/enroll", { method: "POST" });
            setHealth(enrolled.otpauth_uri);
          } catch (err) {
            setError(err instanceof Error ? err.message : "MFA enrollment failed");
          }
        }}
      >
        Enroll authenticator
      </button>
    </CommunicationsFrame>
  );
}
