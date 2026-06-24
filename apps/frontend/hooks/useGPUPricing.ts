"use client"

import { useQuery } from "@tanstack/react-query"

import { api } from "@/lib/api"
import type { GpuPricingResponse } from "@/types"

const GPU_INSTANCES_QUERY_KEY = ["gpu-instances"] as const

async function listGpuInstancesRequest(): Promise<GpuPricingResponse[]> {
  const { data } = await api.get<GpuPricingResponse[]>("/api/v1/gpu/instances")
  return data
}

export function useGPUPricing() {
  return useQuery({
    queryKey: GPU_INSTANCES_QUERY_KEY,
    queryFn: listGpuInstancesRequest,
  })
}
