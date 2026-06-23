"use client"

import { useMemo, useState } from "react"
import { useParams } from "next/navigation"

import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { MetricComparisonChart } from "@/components/charts/MetricComparisonChart"
import { PageContainer } from "@/components/layout/PageContainer"
import { JobStatusBadge } from "@/components/training/JobStatusBadge"
import {
  useCreateExperimentRun,
  useExperiment,
  useExperimentCompare,
} from "@/hooks/useExperiments"
import { useJobs } from "@/hooks/useJobs"
import { getErrorDetail } from "@/lib/utils"

const METRIC_LABELS: Record<string, string> = {
  train_loss: "Train loss",
  eval_loss: "Eval loss",
  gpu_utilization_pct: "GPU utilization (%)",
  vram_used_gb: "VRAM used (GB)",
  tokens_per_second: "Tokens / second",
}

function runLabel(baseModelId: string, methodology: string): string {
  const modelName = baseModelId.split("/").pop() ?? baseModelId
  return `${modelName} (${methodology})`
}

function metricValue(metrics: Record<string, unknown> | null, field: string): string {
  const value = metrics?.[field]
  return typeof value === "number" ? value.toFixed(4) : "—"
}

export default function ExperimentDetailPage() {
  const { experimentId } = useParams<{ experimentId: string }>()
  const experimentQuery = useExperiment(experimentId)
  const compareQuery = useExperimentCompare(experimentId)
  const jobsQuery = useJobs()
  const createRun = useCreateExperimentRun(experimentId)

  const [selectedJobId, setSelectedJobId] = useState<string | null>(null)
  const [attachError, setAttachError] = useState<string | null>(null)

  const attachedJobIds = useMemo(
    () => new Set((compareQuery.data?.runs ?? []).map((run) => run.fine_tune_job_id)),
    [compareQuery.data]
  )
  const attachableJobs = (jobsQuery.data ?? []).filter((job) => !attachedJobIds.has(job.id))

  async function handleAttach() {
    if (!selectedJobId) return
    setAttachError(null)
    try {
      await createRun.mutateAsync({ experimentId, fine_tune_job_id: selectedJobId })
      setSelectedJobId(null)
    } catch (error) {
      setAttachError(getErrorDetail(error, "Unable to attach job as a run."))
    }
  }

  if (experimentQuery.isLoading) {
    return (
      <PageContainer>
        <p className="text-sm text-muted-foreground">Loading experiment...</p>
      </PageContainer>
    )
  }

  if (experimentQuery.isError || !experimentQuery.data) {
    return (
      <PageContainer>
        <Alert variant="destructive">
          <AlertDescription>
            {getErrorDetail(experimentQuery.error, "Experiment not found.")}
          </AlertDescription>
        </Alert>
      </PageContainer>
    )
  }

  const experiment = experimentQuery.data
  const runs = compareQuery.data?.runs ?? []
  const metricsByName = compareQuery.data?.metrics_by_name ?? {}
  const runLabelById = new Map(
    runs.map((run) => [run.run_id, runLabel(run.base_model_id, run.methodology)])
  )

  return (
    <PageContainer>
      <h1 className="text-2xl font-semibold text-foreground">{experiment.name}</h1>
      {experiment.description ? (
        <p className="mt-1 text-sm text-muted-foreground">{experiment.description}</p>
      ) : null}

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Attach a job as a run</CardTitle>
        </CardHeader>
        <CardContent>
          {attachError ? (
            <Alert variant="destructive" className="mb-4">
              <AlertDescription>{attachError}</AlertDescription>
            </Alert>
          ) : null}
          <div className="flex items-center gap-3">
            <Select value={selectedJobId ?? ""} onValueChange={(value) => setSelectedJobId(value)}>
              <SelectTrigger className="w-full max-w-sm">
                <SelectValue placeholder="Select a fine-tune job" />
              </SelectTrigger>
              <SelectContent>
                {attachableJobs.map((job) => (
                  <SelectItem key={job.id} value={job.id}>
                    {runLabel(job.base_model_id, job.methodology)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button
              onClick={handleAttach}
              disabled={!selectedJobId || createRun.isPending}
            >
              {createRun.isPending ? "Attaching..." : "Attach as run"}
            </Button>
          </div>
          {jobsQuery.data && attachableJobs.length === 0 ? (
            <p className="mt-3 text-sm text-muted-foreground">
              All of your jobs are already attached to this experiment.
            </p>
          ) : null}
        </CardContent>
      </Card>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Runs</CardTitle>
        </CardHeader>
        <CardContent>
          {runs.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No runs attached yet — attach a job above to start tracking it here.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Model</TableHead>
                  <TableHead>Methodology</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Train loss</TableHead>
                  <TableHead>Eval loss</TableHead>
                  <TableHead>Attached</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {runs.map((run) => (
                  <TableRow key={run.run_id}>
                    <TableCell className="font-medium">{run.base_model_id}</TableCell>
                    <TableCell>{run.methodology.toUpperCase()}</TableCell>
                    <TableCell>
                      <JobStatusBadge status={run.status} />
                    </TableCell>
                    <TableCell>{metricValue(run.metrics, "train_loss")}</TableCell>
                    <TableCell>{metricValue(run.metrics, "eval_loss")}</TableCell>
                    <TableCell>{new Date(run.created_at).toLocaleString()}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <div className="mt-6 grid grid-cols-1 gap-6 sm:grid-cols-2">
        {Object.entries(metricsByName).map(([metricName, points]) => (
          <Card key={metricName}>
            <CardHeader>
              <CardTitle>{METRIC_LABELS[metricName] ?? metricName}</CardTitle>
            </CardHeader>
            <CardContent>
              <MetricComparisonChart
                data={points.map((point) => {
                  const runId = String(point.run_id)
                  return {
                    run_id: runId,
                    value: Number(point.value),
                    label: runLabelById.get(runId) ?? runId.slice(0, 8),
                  }
                })}
              />
            </CardContent>
          </Card>
        ))}
      </div>
    </PageContainer>
  )
}
