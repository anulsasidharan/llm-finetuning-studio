"use client"

import { useCallback } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { api, clearTokens, getAccessToken, setTokens } from "@/lib/api"
import type { TokenResponse, UserResponse } from "@/types"

interface LoginInput {
  email: string
  password: string
}

interface RegisterInput {
  email: string
  password: string
  full_name: string
}

const ME_QUERY_KEY = ["auth", "me"] as const

async function fetchCurrentUser(): Promise<UserResponse> {
  const { data } = await api.get<UserResponse>("/api/v1/auth/me")
  return data
}

async function loginRequest(input: LoginInput): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>("/api/v1/auth/login", input)
  return data
}

async function registerRequest(input: RegisterInput): Promise<UserResponse> {
  const { data } = await api.post<UserResponse>("/api/v1/auth/register", input)
  return data
}

async function logoutRequest(): Promise<void> {
  await api.post("/api/v1/auth/logout")
}

export function useAuth() {
  const queryClient = useQueryClient()

  const meQuery = useQuery({
    queryKey: ME_QUERY_KEY,
    queryFn: fetchCurrentUser,
    enabled: Boolean(getAccessToken()),
    retry: false,
  })

  const loginMutation = useMutation({
    mutationFn: loginRequest,
    onSuccess: (tokens) => {
      setTokens(tokens.access_token, tokens.refresh_token)
      return queryClient.invalidateQueries({ queryKey: ME_QUERY_KEY })
    },
  })

  const registerMutation = useMutation({
    mutationFn: registerRequest,
  })

  const logout = useCallback(async () => {
    try {
      await logoutRequest()
    } finally {
      clearTokens()
      queryClient.removeQueries({ queryKey: ME_QUERY_KEY })
    }
  }, [queryClient])

  return {
    user: meQuery.data ?? null,
    isLoadingUser: meQuery.isLoading,
    isAuthenticated: Boolean(meQuery.data),
    login: loginMutation.mutateAsync,
    isLoggingIn: loginMutation.isPending,
    loginError: loginMutation.error,
    register: registerMutation.mutateAsync,
    isRegistering: registerMutation.isPending,
    registerError: registerMutation.error,
    logout,
  }
}
