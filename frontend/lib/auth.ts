export type AuthUser = {
  id: string
  username: string
  email: string
  role: "admin" | "dispatcher" | "driver" | "viewer"
  is_active: boolean
}

type ApiErrorBody = {
  detail?: string
}

const RAW_API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"
const API_BASE_URL = RAW_API_BASE.endsWith("/api/v1")
  ? RAW_API_BASE
  : `${RAW_API_BASE}/api/v1`

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  })

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`
    try {
      const body = (await response.json()) as ApiErrorBody
      if (body?.detail) {
        detail = body.detail
      }
    } catch {
      // Ignore JSON parse errors and keep fallback message.
    }
    throw new Error(detail)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

export async function login(username: string, password: string): Promise<void> {
  await apiFetch("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  })
}

export async function register(username: string, email: string, password: string): Promise<void> {
  await apiFetch("/auth/register", {
    method: "POST",
    body: JSON.stringify({ username, email, password }),
  })
}

export async function logout(): Promise<void> {
  await apiFetch("/auth/logout", { method: "POST" })
}

export async function getCurrentUser(): Promise<AuthUser> {
  return apiFetch<AuthUser>("/auth/me")
}
