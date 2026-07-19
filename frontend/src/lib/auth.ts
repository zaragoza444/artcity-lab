const TOKEN_KEY = "artcity_access_token";
const REFRESH_KEY = "artcity_refresh_token";
const USER_KEY = "artcity_user";

export type AuthUser = {
  user_id: string;
  email: string;
  full_name: string;
  role: string;
};

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_KEY);
}

export function getStoredUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
}

export function setSession(tokens: {
  access_token: string;
  refresh_token: string;
  user_id: string;
  email: string;
  full_name: string;
  role: string;
}) {
  localStorage.setItem(TOKEN_KEY, tokens.access_token);
  localStorage.setItem(REFRESH_KEY, tokens.refresh_token);
  localStorage.setItem(
    USER_KEY,
    JSON.stringify({
      user_id: tokens.user_id,
      email: tokens.email,
      full_name: tokens.full_name,
      role: tokens.role,
    })
  );
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(USER_KEY);
}
