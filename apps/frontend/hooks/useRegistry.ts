"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { api } from "@/lib/api"
import type {
  ExportGGUFRequest,
  ModelRegistryCreate,
  ModelRegistryResponse,
  PushHFRequest,
} from "@/types"

const REGISTRY_QUERY_KEY = ["registry"] as const
const registryEntryQueryKey = (entryId: string) => ["registry", entryId] as const

async function listRegistryRequest(): Promise<ModelRegistryResponse[]> {
  const { data } = await api.get<ModelRegistryResponse[]>("/api/v1/registry")
  return data
}

async function getRegistryEntryRequest(entryId: string): Promise<ModelRegistryResponse> {
  const { data } = await api.get<ModelRegistryResponse>(`/api/v1/registry/${entryId}`)
  return data
}

async function createRegistryEntryRequest(
  input: ModelRegistryCreate,
): Promise<ModelRegistryResponse> {
  const { data } = await api.post<ModelRegistryResponse>("/api/v1/registry", input)
  return data
}

async function pushToHFRequest(
  entryId: string,
  payload: PushHFRequest,
): Promise<ModelRegistryResponse> {
  const { data } = await api.post<ModelRegistryResponse>(
    `/api/v1/registry/${entryId}/push-hf`,
    payload,
  )
  return data
}

async function exportToGGUFRequest(
  entryId: string,
  payload: ExportGGUFRequest,
): Promise<ModelRegistryResponse> {
  const { data } = await api.post<ModelRegistryResponse>(
    `/api/v1/registry/${entryId}/export-gguf`,
    payload,
  )
  return data
}

async function deleteRegistryEntryRequest(entryId: string): Promise<void> {
  await api.delete(`/api/v1/registry/${entryId}`)
}

export function useRegistryEntries() {
  return useQuery({
    queryKey: REGISTRY_QUERY_KEY,
    queryFn: listRegistryRequest,
  })
}

export function useRegistryEntry(entryId: string) {
  return useQuery({
    queryKey: registryEntryQueryKey(entryId),
    queryFn: () => getRegistryEntryRequest(entryId),
    enabled: Boolean(entryId),
  })
}

export function useCreateRegistryEntry() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: createRegistryEntryRequest,
    onSuccess: (entry) => {
      queryClient.setQueryData(registryEntryQueryKey(entry.id), entry)
      return queryClient.invalidateQueries({ queryKey: REGISTRY_QUERY_KEY })
    },
  })
}

export function usePushToHF() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ entryId, payload }: { entryId: string; payload: PushHFRequest }) =>
      pushToHFRequest(entryId, payload),
    onSuccess: (entry) => {
      queryClient.setQueryData(registryEntryQueryKey(entry.id), entry)
      return queryClient.invalidateQueries({ queryKey: REGISTRY_QUERY_KEY })
    },
  })
}

export function useExportToGGUF() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ entryId, payload }: { entryId: string; payload: ExportGGUFRequest }) =>
      exportToGGUFRequest(entryId, payload),
    onSuccess: (entry) => {
      queryClient.setQueryData(registryEntryQueryKey(entry.id), entry)
      return queryClient.invalidateQueries({ queryKey: REGISTRY_QUERY_KEY })
    },
  })
}

export function useDeleteRegistryEntry() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: deleteRegistryEntryRequest,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: REGISTRY_QUERY_KEY }),
  })
}
