"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { api } from "@/lib/api"
import type { FineTuneJobResponse, Methodology } from "@/types"

const JOBS_QUERY_KEY = ["jobs"] as const
const jobQueryKey = (jobId: string) => ["jobs", jobId] as const

export type CreateJobInput = {
  base_model_id: string
  methodology: Methodology
  training_config: Record<string, unknown>
  dataset_id?: string | null
  gpu_type?: string | null
  cloud_vendor?: string | null
}

async function listJobsRequest(): Promise<FineTuneJobResponse[]> {
  const { data } = await api.get<FineTuneJobResponse[]>("/api/v1/jobs")
  return data
}

async function getJobRequest(jobId: string): Promise<FineTuneJobResponse> {
  const { data } = await api.get<FineTuneJobResponse>(`/api/v1/jobs/${jobId}`)
  return data
}

async function createJobRequest(input: CreateJobInput): Promise<FineTuneJobResponse> {
  const { data } = await api.post<FineTuneJobResponse>("/api/v1/jobs", input)
  return data
}

export function useJobs() {
  return useQuery({
    queryKey: JOBS_QUERY_KEY,
    queryFn: listJobsRequest,
  })
}

export function useJob(jobId: string) {
  return useQuery({
    queryKey: jobQueryKey(jobId),
    queryFn: () => getJobRequest(jobId),
    enabled: Boolean(jobId),
  })
}

export function useCreateJob() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: createJobRequest,
    onSuccess: (job) => {
      queryClient.setQueryData(jobQueryKey(job.id), job)
      return queryClient.invalidateQueries({ queryKey: JOBS_QUERY_KEY })
    },
  })
}
