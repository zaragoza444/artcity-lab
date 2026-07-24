"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { BrandMark } from "@/components/BrandMark";
import { api } from "@/lib/api";
import { setSession } from "@/lib/auth";

export default function SignupPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [accept, setAccept] = useState(false);
  const [emailToken, setEmailToken] = useState("");
  const [phoneCode, setPhoneCode] = useState("");
  const [step, setStep] = useState<"form" | "verify">("form");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSignup(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const res = await api.signup({
        email,
        full_name: fullName,
        phone_number: phone,
        password,
        accept_terms: accept,
      });
      setMessage(res.message);
      if (res.email_token) setEmailToken(res.email_token);
      if (res.phone_code) setPhoneCode(res.phone_code);
      setStep("verify");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Signup failed");
    } finally {
      setBusy(false);
    }
  }

  async function onVerify(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.verifyEmail(email, emailToken);
      await api.verifyPhone(email, phoneCode);
      const tokens = await api.login(email, password);
      setSession(tokens);
      router.replace("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Verification failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="ac-container flex min-h-[100dvh] flex-col justify-center py-16">
      <div className="mx-auto w-full max-w-md">
        <BrandMark product="platform" />
        <h1 className="mt-10 font-[family-name:var(--font-display)] text-3xl text-[var(--paper)]">
          Customer sign up
        </h1>
        <p className="mt-2 text-sm text-[var(--mist)]">
          Email and phone verification required before Cinema, Studio, and Edit production access.
        </p>

        {step === "form" ? (
          <form onSubmit={onSignup} className="mt-8 space-y-4">
            <label className="block text-xs uppercase tracking-[0.14em] text-[var(--mist)]">
              Full name
              <input
                className="mt-2 w-full border border-[var(--line)] bg-[var(--ink-soft)] px-3 py-2 text-[var(--paper)]"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
              />
            </label>
            <label className="block text-xs uppercase tracking-[0.14em] text-[var(--mist)]">
              Email
              <input
                className="mt-2 w-full border border-[var(--line)] bg-[var(--ink-soft)] px-3 py-2 text-[var(--paper)]"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </label>
            <label className="block text-xs uppercase tracking-[0.14em] text-[var(--mist)]">
              Phone
              <input
                className="mt-2 w-full border border-[var(--line)] bg-[var(--ink-soft)] px-3 py-2 text-[var(--paper)]"
                type="tel"
                placeholder="+9647xxxxxxxx"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                required
              />
            </label>
            <label className="block text-xs uppercase tracking-[0.14em] text-[var(--mist)]">
              Password
              <input
                className="mt-2 w-full border border-[var(--line)] bg-[var(--ink-soft)] px-3 py-2 text-[var(--paper)]"
                type="password"
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </label>
            <label className="flex items-start gap-3 text-sm text-[var(--mist)]">
              <input
                type="checkbox"
                className="mt-1"
                checked={accept}
                onChange={(e) => setAccept(e.target.checked)}
                required
              />
              I accept Art City Terms, Privacy, and rights declarations.
            </label>
            {error ? <p className="text-sm text-[var(--danger)]">{error}</p> : null}
            <button
              type="submit"
              disabled={busy || !accept}
              className="w-full border border-[var(--gold)] bg-[rgba(197,161,94,0.16)] px-4 py-3 text-sm uppercase tracking-[0.14em] text-[var(--gold-bright)] disabled:opacity-50"
            >
              {busy ? "Creating…" : "Create account"}
            </button>
          </form>
        ) : (
          <form onSubmit={onVerify} className="mt-8 space-y-4">
            {message ? <p className="text-sm text-[var(--mist)]">{message}</p> : null}
            <label className="block text-xs uppercase tracking-[0.14em] text-[var(--mist)]">
              Email verification token
              <input
                className="mt-2 w-full border border-[var(--line)] bg-[var(--ink-soft)] px-3 py-2 text-[var(--paper)]"
                value={emailToken}
                onChange={(e) => setEmailToken(e.target.value)}
                required
              />
            </label>
            <label className="block text-xs uppercase tracking-[0.14em] text-[var(--mist)]">
              Phone verification code
              <input
                className="mt-2 w-full border border-[var(--line)] bg-[var(--ink-soft)] px-3 py-2 text-[var(--paper)]"
                value={phoneCode}
                onChange={(e) => setPhoneCode(e.target.value)}
                required
              />
            </label>
            {error ? <p className="text-sm text-[var(--danger)]">{error}</p> : null}
            <button
              type="submit"
              disabled={busy}
              className="w-full border border-[var(--gold)] bg-[rgba(197,161,94,0.16)] px-4 py-3 text-sm uppercase tracking-[0.14em] text-[var(--gold-bright)] disabled:opacity-50"
            >
              {busy ? "Verifying…" : "Verify & enter production"}
            </button>
          </form>
        )}

        <p className="mt-6 text-sm text-[var(--mist)]">
          Already verified?{" "}
          <Link href="/login" className="text-[var(--gold-bright)]">
            Sign in
          </Link>
        </p>
      </div>
    </main>
  );
}
