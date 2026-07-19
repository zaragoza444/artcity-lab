"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import {
  AuthUser,
  clearSession,
  getAccessToken,
  getStoredUser,
  setSession,
} from "@/lib/auth";
import { api } from "@/lib/api";

type AuthContextValue = {
  user: AuthUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

const PUBLIC_PATHS = new Set(["/login"]);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    const stored = getStoredUser();
    const token = getAccessToken();
    if (stored && token) {
      setUser(stored);
      setLoading(false);
      return;
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    if (loading) return;
    if (PUBLIC_PATHS.has(pathname)) return;
    if (!getAccessToken()) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
    }
  }, [loading, pathname, router]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      login: async (email, password) => {
        const res = await api.login(email, password);
        setSession(res);
        setUser({
          user_id: res.user_id,
          email: res.email,
          full_name: res.full_name,
          role: res.role,
        });
      },
      logout: () => {
        clearSession();
        setUser(null);
        router.replace("/login");
      },
    }),
    [user, loading, router]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth requires AuthProvider");
  return ctx;
}
