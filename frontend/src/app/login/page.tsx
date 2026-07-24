"use client";

import { FormEvent, Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { BrandMark } from "@/components/BrandMark";
import { useAuth } from "@/components/AuthProvider";

function LoginForm() {
  const { login } = useAuth();
  const router = useRouter();
  const params = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(email, password);
      router.replace(params.get("next") || "/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="mt-8 space-y-4">
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
        Password
        <input
          className="mt-2 w-full border border-[var(--line)] bg-[var(--ink-soft)] px-3 py-2 text-[var(--paper)]"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
      </label>
      {error ? <p className="text-sm text-[var(--danger)]">{error}</p> : null}
      <button
        type="submit"
        disabled={busy}
        className="w-full border border-[var(--gold)] bg-[rgba(197,161,94,0.16)] px-4 py-3 text-sm uppercase tracking-[0.14em] text-[var(--gold-bright)] disabled:opacity-50"
      >
        {busy ? "Signing in…" : "Sign in"}
      </button>
    </form>
  );
}

export default function LoginPage() {
  return (
    <main className="ac-container flex min-h-[100dvh] flex-col justify-center py-16">
      <div className="mx-auto w-full max-w-md">
        <BrandMark product="platform" />
        <h1 className="mt-10 font-[family-name:var(--font-display)] text-3xl text-[var(--paper)]">
          Art City sign in
        </h1>
        <p className="mt-2 text-sm text-[var(--mist)]">
          Private production OS and AI Core. Customers sign up with email + phone verification.
        </p>
        <Suspense fallback={<p className="mt-8 text-[var(--mist)]">Loading…</p>}>
          <LoginForm />
        </Suspense>
        <p className="mt-6 text-sm text-[var(--mist)]">
          New customer?{" "}
          <a href="/signup" className="text-[var(--gold-bright)]">
            Create account
          </a>
        </p>
      </div>
    </main>
  );
}
