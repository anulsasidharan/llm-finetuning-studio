"use client"

import { useParams } from "next/navigation"

import { Alert, AlertDescription } from "@/components/ui/alert"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { GPUUtilChart } from "@/components/charts/GPUUtilChart"
import { LossChart } from "@/components/charts/LossChart"
import { VRAMChart } from "@/components/charts/VRAMChart"
import { PageContainer } from "@/components/layout/PageContainer"
import { JobStatusBadge } from "@/components/training/JobStatusBadge"
import { useJob } from "@/hooks/useJobs"
import { useTrainingSocket } from "@/lib/websocket"
import { getErrorDetail } from "@/lib/utils"
import type { FineTuneJobStatus } from "@/types"

const TERMINAL_STATUSES: FineTuneJobStatus[] = ["completed", "failed", "cancelled"]

export default function TrainingDashboardPage() {
  const { jobId } = useParams<{ jobId: string }>()
  const jobQuery = useJob(jobId)
  const job = jobQuery.data

  const isTerminal = job ? TERMINAL_STATUSES.includes(job.status) : false
  const socket = useTrainingSocket(jobId, Boolean(job) && !isTerminal)

  if (jobQuery.isLoading) {
    return (
      <PageContainer>
        <p className="text-sm text-muted-foreground">Loading job...</p>
      </PageContainer>
    )
  }

  if (jobQuery.isError || !job) {
    return (
      <PageContainer>
        <Alert variant="destructive">
          <AlertDescription>{getErrorDetail(jobQuery.error, "Job not found.")}</AlertDescription>
        </Alert>
      </PageContainer>
    )
  }

  const liveStatus = socket.status ?? job.status
  const latest = socket.metrics.at(-1)

  return (
    <PageContainer>
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-semibold text-foreground">{job.base_model_id}</h1>
        <JobStatusBadge status={liveStatus} />
      </div>
      <p className="mt-1 text-sm text-muted-foreground">
        {job.methodology.toUpperCase()} · created {new Date(job.created_at).toLocaleString()}
      </p>

      {isTerminal && (
        <Alert className="mt-4">
          <AlertDescription>
            This job has already finished — no further live updates will arrive.
          </AlertDescription>
        </Alert>
      )}
      {!isTerminal && socket.connectionState === "error" && (
        <Alert variant="destructive" className="mt-4">
          <AlertDescription>
            Couldn&apos;t connect to the live metrics socket. Refresh the page to retry.
          </AlertDescription>
        </Alert>
      )}

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">Step</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-semibold">{latest?.step ?? "—"}</CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">GPU utilization</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-semibold">
            {latest?.gpu_utilization_pct != null ? `${latest.gpu_utilization_pct.toFixed(0)}%` : "—"}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">VRAM used</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-semibold">
            {latest?.vram_used_gb != null ? `${latest.vram_used_gb.toFixed(1)} GB` : "—"}
          </CardContent>
        </Card>
      </div>

      <div className="mt-6 flex flex-col gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Loss</CardTitle>
          </CardHeader>
          <CardContent>
            <LossChart data={socket.metrics} />
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>GPU utilization</CardTitle>
            </CardHeader>
            <CardContent>
              <GPUUtilChart data={socket.metrics} />
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>VRAM used</CardTitle>
            </CardHeader>
            <CardContent>
              <VRAMChart data={socket.metrics} />
            </CardContent>
          </Card>
        </div>
      </div>
    </PageContainer>
  )
}
