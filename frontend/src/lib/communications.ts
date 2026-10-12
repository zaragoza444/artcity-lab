import { getAccessToken } from "@/lib/auth";
import { refreshAccessSession } from "@/lib/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function commRequest<T>(path: string, init?: RequestInit, retried = false): Promise<T> {
  const headers = new Headers(init?.headers);
  if (!(init?.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const token = getAccessToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const res = await fetch(`${API_URL}/api/v1/communications${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });
  if (res.status === 401 && !retried) {
    const refreshed = await refreshAccessSession();
    if (refreshed) return commRequest<T>(path, init, true);
  }
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed (${res.status})`);
  }
  const type = res.headers.get("content-type") || "";
  if (type.includes("text/csv") || type.includes("text/plain")) return (await res.text()) as T;
  return (await res.json()) as T;
}
