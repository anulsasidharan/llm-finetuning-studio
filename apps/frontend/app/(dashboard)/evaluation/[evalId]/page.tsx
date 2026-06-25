"use client"

import { useParams } from "next/navigation"

import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { PageContainer } from "@/components/layout/PageContainer"
import { useEvalJob } from "@/hooks/useEval"
import { getErrorDetail } from "@/lib/utils"
import type { EvalJobStatus } from "@/types"

const STATUS_VARIANT: Record<EvalJobStatus, "default" | "secondary" | "destructive" | "outline"> = {
  pending: "outline",
  queued: "secondary",
  running: "secondary",
  completed: "default",
  failed: "destructive",
}

type CompareCompletion = {
  prompt: string
  base_completion: string
  finetuned_completion: string
}

type MetricRow = { label: string; base: number | null; finetuned: number | null; delta: number | null }

function asRecord(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null ? (value as Record<string, unknown>) : null
}

function asCompletions(result: Record<string, unknown> | null): CompareCompletion[] {
  const raw = result?.completions
  if (!Array.isArray(raw)) return []
  return raw.filter((item): item is CompareCompletion => {
    const record = asRecord(item)
    return record !== null && typeof record.prompt === "string"
  })
}

function flattenNumericMetrics(value: unknown, prefix = ""): { label: string; value: number }[] {
  const record = asRecord(value)
  if (!record) return []
  const rows: { label: string; value: number }[] = []
  for (const [key, child] of Object.entries(record)) {
    const label = prefix ? `${prefix}.${key}` : key
    if (typeof child === "number") {
      rows.push({ label, value: child })
    } else if (typeof child === "object" && child !== null) {
      rows.push(...flattenNumericMetrics(child, label))
    }
  }
  return rows
}

function buildMetricRows(benchmarks: Record<string, unknown> | null): MetricRow[] {
  const base = new Map(flattenNumericMetrics(benchmarks?.base).map((row) => [row.label, row.value]))
  const finetuned = new Map(
    flattenNumericMetrics(benchmarks?.finetuned).map((row) => [row.label, row.value])
  )
  const delta = new Map(flattenNumericMetrics(benchmarks?.delta).map((row) => [row.label, row.value]))
  const labels = new Set([...base.keys(), ...finetuned.keys(), ...delta.keys()])
  return Array.from(labels)
    .sort()
    .map((label) => ({
      label,
      base: base.get(label) ?? null,
      finetuned: finetuned.get(label) ?? null,
      delta: delta.get(label) ?? null,
    }))
}

function formatMetric(value: number | null): string {
  return value === null ? "—" : value.toFixed(4)
}

export default function EvalJobDetailPage() {
  const { evalId } = useParams<{ evalId: string }>()
  const evalJobQuery = useEvalJob(evalId)

  if (evalJobQuery.isLoading) {
    return (
      <PageContainer>
        <p className="text-sm text-muted-foreground">Loading evaluation...</p>
      </PageContainer>
    )
  }

  if (evalJobQuery.isError || !evalJobQuery.data) {
    return (
      <PageContainer>
        <Alert variant="destructive">
          <AlertDescription>
            {getErrorDetail(evalJobQuery.error, "Evaluation not found.")}
          </AlertDescription>
        </Alert>
      </PageContainer>
    )
  }

  const job = evalJobQuery.data
  const result = asRecord(job.result)
  const completions = job.eval_type === "compare" ? asCompletions(result) : []
  const benchmarksBlock = job.eval_type === "compare" ? asRecord(result?.benchmarks) : null
  const benchmarkMetricRows = benchmarksBlock ? buildMetricRows(benchmarksBlock) : []
  const standaloneMetricRows =
    job.eval_type === "benchmark" ? flattenNumericMetrics(result?.metrics) : []
  const isActive = job.status === "pending" || job.status === "queued" || job.status === "running"

  return (
    <PageContainer>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">
            {job.eval_type === "compare" ? "Comparison" : "Benchmark"}
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {job.base_model_id}
            {job.finetuned_model_id ? ` vs. ${job.finetuned_model_id}` : ""}
          </p>
        </div>
        <Badge variant={STATUS_VARIANT[job.status]}>{job.status}</Badge>
      </div>

      {job.status === "failed" && job.error_message ? (
        <Alert variant="destructive" className="mt-6">
          <AlertDescription>{job.error_message}</AlertDescription>
        </Alert>
      ) : null}

      {isActive ? (
        <Card className="mt-6">
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            Evaluation is {job.status} — this page refreshes automatically.
          </CardContent>
        </Card>
      ) : null}

      {job.eval_type === "compare" && completions.length > 0 ? (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Side-by-side completions</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Prompt</TableHead>
                  <TableHead>Base</TableHead>
                  <TableHead>Fine-tuned</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {completions.map((completion, index) => (
                  <TableRow key={index}>
                    <TableCell className="font-medium">{completion.prompt}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {completion.base_completion}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {completion.finetuned_completion}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      ) : null}

      {benchmarkMetricRows.length > 0 ? (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Benchmark deltas</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Metric</TableHead>
                  <TableHead>Base</TableHead>
                  <TableHead>Fine-tuned</TableHead>
                  <TableHead>Delta</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {benchmarkMetricRows.map((row) => (
                  <TableRow key={row.label}>
                    <TableCell className="font-medium">{row.label}</TableCell>
                    <TableCell>{formatMetric(row.base)}</TableCell>
                    <TableCell>{formatMetric(row.finetuned)}</TableCell>
                    <TableCell>{formatMetric(row.delta)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      ) : null}

      {job.eval_type === "benchmark" && standaloneMetricRows.length > 0 ? (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Benchmark results</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Metric</TableHead>
                  <TableHead>Value</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {standaloneMetricRows.map((row) => (
                  <TableRow key={row.label}>
                    <TableCell className="font-medium">{row.label}</TableCell>
                    <TableCell>{formatMetric(row.value)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      ) : null}
    </PageContainer>
  )
}
