"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { api } from "@/lib/api"
import type {
  ExperimentCompareResponse,
  ExperimentResponse,
  ExperimentRunResponse,
} from "@/types"

const EXPERIMENTS_QUERY_KEY = ["experiments"] as const
const experimentQueryKey = (experimentId: string) => ["experiments", experimentId] as const
const experimentCompareQueryKey = (experimentId: string) =>
  ["experiments", experimentId, "compare"] as const

export type CreateExperimentInput = {
  name: string
  description?: string | null
}

export type CreateExperimentRunInput = {
  experimentId: string
  fine_tune_job_id: string
}

async function listExperimentsRequest(): Promise<ExperimentResponse[]> {
  const { data } = await api.get<ExperimentResponse[]>("/api/v1/experiments")
  return data
}

async function getExperimentRequest(experimentId: string): Promise<ExperimentResponse> {
  const { data } = await api.get<ExperimentResponse>(`/api/v1/experiments/${experimentId}`)
  return data
}

async function createExperimentRequest(
  input: CreateExperimentInput
): Promise<ExperimentResponse> {
  const { data } = await api.post<ExperimentResponse>("/api/v1/experiments", input)
  return data
}

async function createExperimentRunRequest(
  input: CreateExperimentRunInput
): Promise<ExperimentRunResponse> {
  const { data } = await api.post<ExperimentRunResponse>(
    `/api/v1/experiments/${input.experimentId}/runs`,
    { fine_tune_job_id: input.fine_tune_job_id }
  )
  return data
}

async function compareExperimentRequest(
  experimentId: string
): Promise<ExperimentCompareResponse> {
  const { data } = await api.get<ExperimentCompareResponse>(
    `/api/v1/experiments/${experimentId}/compare`
  )
  return data
}

export function useExperiments() {
  return useQuery({
    queryKey: EXPERIMENTS_QUERY_KEY,
    queryFn: listExperimentsRequest,
  })
}

export function useExperiment(experimentId: string) {
  return useQuery({
    queryKey: experimentQueryKey(experimentId),
    queryFn: () => getExperimentRequest(experimentId),
    enabled: Boolean(experimentId),
  })
}

export function useExperimentCompare(experimentId: string) {
  return useQuery({
    queryKey: experimentCompareQueryKey(experimentId),
    queryFn: () => compareExperimentRequest(experimentId),
    enabled: Boolean(experimentId),
  })
}

export function useCreateExperiment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: createExperimentRequest,
    onSuccess: (experiment) => {
      queryClient.setQueryData(experimentQueryKey(experiment.id), experiment)
      return queryClient.invalidateQueries({ queryKey: EXPERIMENTS_QUERY_KEY })
    },
  })
}

export function useCreateExperimentRun(experimentId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: createExperimentRunRequest,
    onSuccess: () => {
      return queryClient.invalidateQueries({
        queryKey: experimentCompareQueryKey(experimentId),
      })
    },
  })
}
