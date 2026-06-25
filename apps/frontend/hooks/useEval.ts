"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { api } from "@/lib/api"
import type { EvalBenchmarkCreate, EvalCompareCreate, EvalJobResponse } from "@/types"

const EVAL_JOBS_QUERY_KEY = ["eval-jobs"] as const
const evalJobQueryKey = (evalId: string) => ["eval-jobs", evalId] as const

const ACTIVE_STATUSES = new Set(["pending", "queued", "running"])

async function listEvalJobsRequest(): Promise<EvalJobResponse[]> {
  const { data } = await api.get<EvalJobResponse[]>("/api/v1/eval")
  return data
}

async function getEvalJobRequest(evalId: string): Promise<EvalJobResponse> {
  const { data } = await api.get<EvalJobResponse>(`/api/v1/eval/${evalId}`)
  return data
}

async function createCompareJobRequest(input: EvalCompareCreate): Promise<EvalJobResponse> {
  const { data } = await api.post<EvalJobResponse>("/api/v1/eval/compare", input)
  return data
}

async function createBenchmarkJobRequest(input: EvalBenchmarkCreate): Promise<EvalJobResponse> {
  const { data } = await api.post<EvalJobResponse>("/api/v1/eval/benchmark", input)
  return data
}

export function useEvalJobs() {
  return useQuery({
    queryKey: EVAL_JOBS_QUERY_KEY,
    queryFn: listEvalJobsRequest,
  })
}

// Polls every 3s while the job is still in flight, stops once it reaches a terminal
// status -- mirrors the lack of a WebSocket hub for eval jobs (no live push channel,
// see training_engine/utils/eval_status.py), so this is the only way the UI learns
// a queued/running job has finished.
export function useEvalJob(evalId: string) {
  return useQuery({
    queryKey: evalJobQueryKey(evalId),
    queryFn: () => getEvalJobRequest(evalId),
    enabled: Boolean(evalId),
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status && ACTIVE_STATUSES.has(status) ? 3000 : false
    },
  })
}

export function useCreateCompareJob() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: createCompareJobRequest,
    onSuccess: (job) => {
      queryClient.setQueryData(evalJobQueryKey(job.id), job)
      return queryClient.invalidateQueries({ queryKey: EVAL_JOBS_QUERY_KEY })
    },
  })
}

export function useCreateBenchmarkJob() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: createBenchmarkJobRequest,
    onSuccess: (job) => {
      queryClient.setQueryData(evalJobQueryKey(job.id), job)
      return queryClient.invalidateQueries({ queryKey: EVAL_JOBS_QUERY_KEY })
    },
  })
}
