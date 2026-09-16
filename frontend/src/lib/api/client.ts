const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8088').replace(
  /\/$/,
  '',
)

export function apiUrl(path: string) {
  return `${apiBaseUrl}${path}`
}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly payload?: unknown,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(apiUrl(path), {
    ...init,
    headers: {
      Accept: 'application/json',
      ...init?.headers,
    },
  })

  const payload: unknown = await response.json().catch(() => undefined)
  if (!response.ok) {
    const message =
      typeof payload === 'object' && payload !== null && 'error' in payload
        ? String((payload.error as { message?: unknown }).message ?? 'Erro na API')
        : 'Erro na API'
    throw new ApiError(message, response.status, payload)
  }
  return payload as T
}
