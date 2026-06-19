import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios"

const ACCESS_TOKEN_STORAGE_KEY = "fts_access_token"
const REFRESH_TOKEN_STORAGE_KEY = "fts_refresh_token"

// Requests to these paths must never trigger the refresh-and-retry flow below
// (refresh itself would recurse; login/register 401s are real auth failures).
const AUTH_PATHS_EXEMPT_FROM_REFRESH = [
  "/api/v1/auth/login",
  "/api/v1/auth/register",
  "/api/v1/auth/refresh",
]

type RetryableRequestConfig = InternalAxiosRequestConfig & { _retry?: boolean }

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null
  return window.localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY)
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null
  return window.localStorage.getItem(REFRESH_TOKEN_STORAGE_KEY)
}

export function setTokens(accessToken: string, refreshToken: string): void {
  if (typeof window === "undefined") return
  window.localStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, accessToken)
  window.localStorage.setItem(REFRESH_TOKEN_STORAGE_KEY, refreshToken)
}

export function clearTokens(): void {
  if (typeof window === "undefined") return
  window.localStorage.removeItem(ACCESS_TOKEN_STORAGE_KEY)
  window.localStorage.removeItem(REFRESH_TOKEN_STORAGE_KEY)
}

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
})

api.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Single-flight guard so concurrent 401s only trigger one /auth/refresh call.
let refreshPromise: Promise<string> | null = null

async function refreshAccessToken(): Promise<string> {
  const refreshToken = getRefreshToken()
  if (!refreshToken) {
    throw new Error("No refresh token available.")
  }

  // Plain axios (not the `api` instance) — avoids recursing through these
  // same interceptors and doesn't need an Authorization header.
  const { data } = await axios.post<{ access_token: string; refresh_token: string }>(
    `${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/refresh`,
    { refresh_token: refreshToken }
  )
  setTokens(data.access_token, data.refresh_token)
  return data.access_token
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as RetryableRequestConfig | undefined
    const isExemptPath = AUTH_PATHS_EXEMPT_FROM_REFRESH.some((path) =>
      originalRequest?.url?.includes(path)
    )

    if (
      error.response?.status !== 401 ||
      !originalRequest ||
      originalRequest._retry ||
      isExemptPath
    ) {
      return Promise.reject(error)
    }

    originalRequest._retry = true

    try {
      refreshPromise ??= refreshAccessToken().finally(() => {
        refreshPromise = null
      })
      const newAccessToken = await refreshPromise
      originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
      return api(originalRequest)
    } catch (refreshError) {
      clearTokens()
      if (typeof window !== "undefined") {
        window.location.href = "/login"
      }
      return Promise.reject(refreshError)
    }
  }
)
