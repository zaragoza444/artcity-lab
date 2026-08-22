"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import {
  AuthUser,
  SESSION_EXPIRED_EVENT,
  SESSION_UPDATED_EVENT,
  clearSession,
  getAccessToken,
  getRefreshToken,
  getStoredUser,
  setSession,
} from "@/lib/auth";
import { api, refreshAccessSession } from "@/lib/api";

type AuthContextValue = {
  user: AuthUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

const PUBLIC_PATHS = new Set(["/", "/login", "/signup"]);

function toAuthUser(u: {
  user_id?: string;
  id?: string;
  email: string;
  full_name: string;
  role: string;
}): AuthUser {
  return {
    user_id: u.user_id || u.id || "",
    email: u.email,
    full_name: u.full_name,
    role: u.role,
  };
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    let cancelled = false;

    async function boot() {
      const stored = getStoredUser();
      const token = getAccessToken();
      if (!stored || !token) {
        if (!cancelled) {
          setUser(null);
          setLoading(false);
        }
        return;
      }

      try {
        const me = await api.me();
        if (cancelled) return;
        setUser(
          toAuthUser({
            id: me.id,
            email: me.email,
            full_name: me.full_name,
            role: me.role,
          }),
        );
      } catch {
        if (getRefreshToken()) {
          const ok = await refreshAccessSession();
          if (ok && !cancelled) {
            const next = getStoredUser();
            setUser(next);
            setLoading(false);
            return;
          }
        }
        clearSession();
        if (!cancelled) setUser(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void boot();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const onUpdated = () => setUser(getStoredUser());
    const onExpired = () => {
      setUser(null);
      if (!PUBLIC_PATHS.has(pathname)) {
        router.replace(`/login?next=${encodeURIComponent(pathname)}`);
      }
    };
    window.addEventListener(SESSION_UPDATED_EVENT, onUpdated);
    window.addEventListener(SESSION_EXPIRED_EVENT, onExpired);
    return () => {
      window.removeEventListener(SESSION_UPDATED_EVENT, onUpdated);
      window.removeEventListener(SESSION_EXPIRED_EVENT, onExpired);
    };
  }, [pathname, router]);

  useEffect(() => {
    if (loading) return;
    if (PUBLIC_PATHS.has(pathname)) return;
    if (!getAccessToken() || !user) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
    }
  }, [loading, pathname, router, user]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      login: async (email, password) => {
        const res = await api.login(email, password);
        setSession(res);
        setUser(
          toAuthUser({
            user_id: res.user_id,
            email: res.email,
            full_name: res.full_name,
            role: res.role,
          }),
        );
      },
      logout: () => {
        clearSession();
        setUser(null);
        router.replace("/login");
      },
    }),
    [user, router],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth requires AuthProvider");
  return ctx;
}
