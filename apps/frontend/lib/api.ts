import axios from "axios"

const ACCESS_TOKEN_STORAGE_KEY = "fts_access_token"

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null
  return window.localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY)
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

// Real 401 handling (redirect/refresh) lands with useAuth in PHASE1-WEEK3-009.
api.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(error)
)
