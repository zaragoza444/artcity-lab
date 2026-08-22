"use client";

import { AuthProvider } from "@/components/AuthProvider";
import { LocaleProvider } from "@/components/LocaleProvider";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <LocaleProvider>
      <AuthProvider>{children}</AuthProvider>
    </LocaleProvider>
  );
}
