"use client"

import { useMutation, useQuery } from "@tanstack/react-query"

import { api } from "@/lib/api"
import type { CostEstimateRequest, CostEstimateResponse, GpuPricingResponse } from "@/types"

async function estimateCostRequest(input: CostEstimateRequest): Promise<CostEstimateResponse> {
  const { data } = await api.post<CostEstimateResponse>("/api/v1/gpu/estimate", input)
  return data
}

export function useCostEstimate() {
  return useMutation({
    mutationFn: estimateCostRequest,
  })
}

/** Fetches a fixed-hours cost estimate for an instance at each of `hoursList`, in parallel. */
export function useCostProjections(instance: GpuPricingResponse | undefined, hoursList: number[]) {
  return useQuery({
    queryKey: ["cost-projections", instance?.vendor, instance?.gpu_type, hoursList],
    queryFn: () =>
      Promise.all(
        hoursList.map((hours) =>
          estimateCostRequest({ vendor: instance!.vendor, gpu_type: instance!.gpu_type, hours })
        )
      ),
    enabled: Boolean(instance),
  })
}
