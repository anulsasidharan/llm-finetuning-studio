"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { api } from "@/lib/api"
import type { DatasetResponse } from "@/types"

const DATASETS_QUERY_KEY = ["datasets"] as const
const datasetQueryKey = (datasetId: string) => ["datasets", datasetId] as const

async function listDatasetsRequest(): Promise<DatasetResponse[]> {
  const { data } = await api.get<DatasetResponse[]>("/api/v1/datasets")
  return data
}

async function getDatasetRequest(datasetId: string): Promise<DatasetResponse> {
  const { data } = await api.get<DatasetResponse>(`/api/v1/datasets/${datasetId}`)
  return data
}

async function uploadDatasetRequest(file: File): Promise<DatasetResponse> {
  const formData = new FormData()
  formData.append("file", file)
  const { data } = await api.post<DatasetResponse>("/api/v1/datasets/upload", formData)
  return data
}

async function formatDatasetRequest(datasetId: string): Promise<DatasetResponse> {
  const { data } = await api.post<DatasetResponse>(`/api/v1/datasets/${datasetId}/format`)
  return data
}

async function qualityCheckDatasetRequest(datasetId: string): Promise<DatasetResponse> {
  const { data } = await api.post<DatasetResponse>(
    `/api/v1/datasets/${datasetId}/quality-check`
  )
  return data
}

export function useDatasets() {
  return useQuery({
    queryKey: DATASETS_QUERY_KEY,
    queryFn: listDatasetsRequest,
  })
}

export function useDataset(datasetId: string) {
  return useQuery({
    queryKey: datasetQueryKey(datasetId),
    queryFn: () => getDatasetRequest(datasetId),
    enabled: Boolean(datasetId),
  })
}

export function useUploadDataset() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: uploadDatasetRequest,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: DATASETS_QUERY_KEY }),
  })
}

export function useFormatDataset(datasetId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => formatDatasetRequest(datasetId),
    onSuccess: (dataset) => {
      queryClient.setQueryData(datasetQueryKey(datasetId), dataset)
      return queryClient.invalidateQueries({ queryKey: DATASETS_QUERY_KEY })
    },
  })
}

export function useQualityCheckDataset(datasetId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => qualityCheckDatasetRequest(datasetId),
    onSuccess: (dataset) => {
      queryClient.setQueryData(datasetQueryKey(datasetId), dataset)
      return queryClient.invalidateQueries({ queryKey: DATASETS_QUERY_KEY })
    },
  })
}
