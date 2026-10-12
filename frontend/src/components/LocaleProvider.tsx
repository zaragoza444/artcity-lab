"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import en from "@/i18n/en/common.json";
import ckb from "@/i18n/ckb-IQ/common.json";
import ar from "@/i18n/ar/common.json";

export type UiLocale = "en" | "ckb-IQ" | "ar";

const dictionaries: Record<UiLocale, Record<string, string>> = {
  en,
  "ckb-IQ": ckb,
  ar,
};

type LocaleContextValue = {
  locale: UiLocale;
  dir: "ltr" | "rtl";
  setLocale: (locale: UiLocale) => void;
  t: (key: string) => string;
};

const LocaleContext = createContext<LocaleContextValue | null>(null);

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<UiLocale>("en");

  useEffect(() => {
    const saved = window.localStorage.getItem("artcity.uiLocale") as UiLocale | null;
    if (saved === "en" || saved === "ckb-IQ" || saved === "ar") setLocaleState(saved);
  }, []);

  const setLocale = useCallback((next: UiLocale) => {
    setLocaleState(next);
    window.localStorage.setItem("artcity.uiLocale", next);
  }, []);

  const dir: "ltr" | "rtl" = locale === "en" ? "ltr" : "rtl";

  useEffect(() => {
    document.documentElement.lang = locale === "ar" ? "ar" : locale === "ckb-IQ" ? "ckb" : "en";
    document.documentElement.dir = dir;
    document.body.dataset.locale = locale;
  }, [locale, dir]);

  const t = useCallback(
    (key: string) => dictionaries[locale][key] || dictionaries.en[key] || key,
    [locale],
  );

  const value = useMemo(
    () => ({ locale, dir, setLocale, t }),
    [locale, dir, setLocale, t],
  );

  return <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>;
}

export function useLocale() {
  const ctx = useContext(LocaleContext);
  if (!ctx) throw new Error("useLocale must be used within LocaleProvider");
  return ctx;
}
