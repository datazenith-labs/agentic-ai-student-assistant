const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";
const TOKEN_KEY = "sage_access_token";

export type AuthUser = { id: string; email: string; name: string };
export type AuthResponse = {
  access_token: string;
  token_type: string;
  user: AuthUser;
};

export function getAccessToken(): string | null {
  return typeof window === "undefined" ? null : localStorage.getItem(TOKEN_KEY);
}

export function saveAccessToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearAccessToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

async function authRequest(path: string, body: object): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE}/api/v1/auth/${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail ?? "Authentication failed.");
  return data as AuthResponse;
}

export const login = (email: string, password: string) =>
  authRequest("login", { email, password });

export const signup = (name: string, email: string, password: string) =>
  authRequest("signup", { name, email, password });

export async function fetchMe(token: string): Promise<AuthUser> {
  const response = await fetch(`${API_BASE}/api/v1/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error("Your session has expired.");
  return response.json();
}
