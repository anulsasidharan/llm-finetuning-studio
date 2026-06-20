"use client"

import { useQuery } from "@tanstack/react-query"

import { api } from "@/lib/api"
import type { ModelCatalogResponse } from "@/types"

const MODEL_CATALOG_QUERY_KEY = ["model-catalog"] as const

async function listModelCatalogRequest(): Promise<ModelCatalogResponse[]> {
  const { data } = await api.get<ModelCatalogResponse[]>("/api/v1/models/catalog")
  return data
}

export function useModelCatalog() {
  return useQuery({
    queryKey: MODEL_CATALOG_QUERY_KEY,
    queryFn: listModelCatalogRequest,
  })
}
