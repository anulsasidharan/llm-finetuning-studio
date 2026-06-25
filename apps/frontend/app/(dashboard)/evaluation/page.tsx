"use client"

import { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { zodResolver } from "@hookform/resolvers/zod"
import { Controller, useForm } from "react-hook-form"
import { z } from "zod"

import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { PageContainer } from "@/components/layout/PageContainer"
import { useCreateBenchmarkJob, useCreateCompareJob, useEvalJobs } from "@/hooks/useEval"
import { useModelCatalog } from "@/hooks/useModelCatalog"
import { getErrorDetail } from "@/lib/utils"
import type { EvalBenchmark, EvalJobStatus } from "@/types"

const BENCHMARK_OPTIONS: EvalBenchmark[] = ["mmlu", "hellaswag", "arc"]

const STATUS_VARIANT: Record<EvalJobStatus, "default" | "secondary" | "destructive" | "outline"> = {
  pending: "outline",
  queued: "secondary",
  running: "secondary",
  completed: "default",
  failed: "destructive",
}

const compareSchema = z.object({
  base_model_id: z.string().min(1, "Select a base model."),
  finetuned_model_id: z.string().min(1, "Enter the fine-tuned model ID or path."),
  prompts: z.string().min(1, "Enter at least one prompt."),
})
type CompareFormValues = z.infer<typeof compareSchema>

const benchmarkSchema = z.object({
  base_model_id: z.string().min(1, "Select a model."),
})
type BenchmarkFormValues = z.infer<typeof benchmarkSchema>

function BenchmarkPicker({
  selected,
  onToggle,
}: {
  selected: Set<EvalBenchmark>
  onToggle: (benchmark: EvalBenchmark) => void
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {BENCHMARK_OPTIONS.map((benchmark) => (
        <Button
          key={benchmark}
          type="button"
          size="sm"
          variant={selected.has(benchmark) ? "default" : "outline"}
          onClick={() => onToggle(benchmark)}
        >
          {benchmark.toUpperCase()}
        </Button>
      ))}
    </div>
  )
}

export default function EvaluationPage() {
  const router = useRouter()
  const modelCatalogQuery = useModelCatalog()
  const evalJobsQuery = useEvalJobs()
  const createCompare = useCreateCompareJob()
  const createBenchmark = useCreateBenchmarkJob()

  const [compareBenchmarks, setCompareBenchmarks] = useState<Set<EvalBenchmark>>(new Set())
  const [benchmarkSelection, setBenchmarkSelection] = useState<Set<EvalBenchmark>>(new Set())
  const [compareError, setCompareError] = useState<string | null>(null)
  const [benchmarkError, setBenchmarkError] = useState<string | null>(null)

  const compareForm = useForm<CompareFormValues>({
    resolver: zodResolver(compareSchema),
    defaultValues: { base_model_id: "", finetuned_model_id: "", prompts: "" },
  })
  const benchmarkForm = useForm<BenchmarkFormValues>({
    resolver: zodResolver(benchmarkSchema),
    defaultValues: { base_model_id: "" },
  })

  function toggleSet(setter: typeof setCompareBenchmarks, benchmark: EvalBenchmark) {
    setter((prev) => {
      const next = new Set(prev)
      if (next.has(benchmark)) next.delete(benchmark)
      else next.add(benchmark)
      return next
    })
  }

  async function onSubmitCompare(values: CompareFormValues) {
    setCompareError(null)
    const prompts = values.prompts
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)
    if (prompts.length === 0) {
      setCompareError("Enter at least one prompt.")
      return
    }
    try {
      const job = await createCompare.mutateAsync({
        base_model_id: values.base_model_id,
        finetuned_model_id: values.finetuned_model_id,
        prompts,
        benchmarks: compareBenchmarks.size > 0 ? Array.from(compareBenchmarks) : null,
        max_new_tokens: 256,
      })
      compareForm.reset()
      setCompareBenchmarks(new Set())
      router.push(`/evaluation/${job.id}`)
    } catch (error) {
      setCompareError(getErrorDetail(error, "Unable to start comparison."))
    }
  }

  async function onSubmitBenchmark(values: BenchmarkFormValues) {
    setBenchmarkError(null)
    if (benchmarkSelection.size === 0) {
      setBenchmarkError("Select at least one benchmark.")
      return
    }
    try {
      const job = await createBenchmark.mutateAsync({
        base_model_id: values.base_model_id,
        benchmarks: Array.from(benchmarkSelection),
      })
      benchmarkForm.reset()
      setBenchmarkSelection(new Set())
      router.push(`/evaluation/${job.id}`)
    } catch (error) {
      setBenchmarkError(getErrorDetail(error, "Unable to start benchmark."))
    }
  }

  return (
    <PageContainer>
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Evaluation Playground</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Compare a base model against a fine-tuned model side-by-side, or run a standalone
          benchmark suite.
        </p>
      </div>

      <Tabs defaultValue="compare" className="mt-6">
        <TabsList>
          <TabsTrigger value="compare">Compare</TabsTrigger>
          <TabsTrigger value="benchmark">Benchmark</TabsTrigger>
        </TabsList>

        <TabsContent value="compare">
          <Card className="mt-4">
            <CardHeader>
              <CardTitle>Base vs. fine-tuned comparison</CardTitle>
            </CardHeader>
            <CardContent>
              <form
                className="flex flex-col gap-4"
                onSubmit={compareForm.handleSubmit(onSubmitCompare)}
                noValidate
              >
                {compareError ? (
                  <Alert variant="destructive">
                    <AlertDescription>{compareError}</AlertDescription>
                  </Alert>
                ) : null}
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="compare-base-model">Base model</Label>
                    <Controller
                      control={compareForm.control}
                      name="base_model_id"
                      render={({ field }) => (
                        <Select
                          value={field.value || null}
                          onValueChange={(value) => field.onChange(value)}
                        >
                          <SelectTrigger id="compare-base-model" className="w-full">
                            <SelectValue placeholder="Select a base model" />
                          </SelectTrigger>
                          <SelectContent>
                            {(modelCatalogQuery.data ?? []).map((model) => (
                              <SelectItem key={model.model_id} value={model.model_id}>
                                {model.display_name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      )}
                    />
                    {compareForm.formState.errors.base_model_id ? (
                      <p className="text-sm text-destructive">
                        {compareForm.formState.errors.base_model_id.message}
                      </p>
                    ) : null}
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="compare-finetuned-model">Fine-tuned model ID or path</Label>
                    <Input
                      id="compare-finetuned-model"
                      placeholder="org/my-finetuned-model"
                      {...compareForm.register("finetuned_model_id")}
                    />
                    {compareForm.formState.errors.finetuned_model_id ? (
                      <p className="text-sm text-destructive">
                        {compareForm.formState.errors.finetuned_model_id.message}
                      </p>
                    ) : null}
                  </div>
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="compare-prompts">Prompts (one per line)</Label>
                  <Textarea
                    id="compare-prompts"
                    rows={5}
                    placeholder={"Explain LoRA in one sentence.\nWrite a haiku about GPUs."}
                    {...compareForm.register("prompts")}
                  />
                  {compareForm.formState.errors.prompts ? (
                    <p className="text-sm text-destructive">
                      {compareForm.formState.errors.prompts.message}
                    </p>
                  ) : null}
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label>Benchmark deltas (optional)</Label>
                  <BenchmarkPicker
                    selected={compareBenchmarks}
                    onToggle={(benchmark) => toggleSet(setCompareBenchmarks, benchmark)}
                  />
                </div>
                <Button type="submit" className="self-start" disabled={createCompare.isPending}>
                  {createCompare.isPending ? "Starting..." : "Run comparison"}
                </Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="benchmark">
          <Card className="mt-4">
            <CardHeader>
              <CardTitle>Standalone benchmark</CardTitle>
            </CardHeader>
            <CardContent>
              <form
                className="flex flex-col gap-4"
                onSubmit={benchmarkForm.handleSubmit(onSubmitBenchmark)}
                noValidate
              >
                {benchmarkError ? (
                  <Alert variant="destructive">
                    <AlertDescription>{benchmarkError}</AlertDescription>
                  </Alert>
                ) : null}
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="benchmark-base-model">Model</Label>
                  <Controller
                    control={benchmarkForm.control}
                    name="base_model_id"
                    render={({ field }) => (
                      <Select
                        value={field.value || null}
                        onValueChange={(value) => field.onChange(value)}
                      >
                        <SelectTrigger id="benchmark-base-model" className="w-full max-w-sm">
                          <SelectValue placeholder="Select a model" />
                        </SelectTrigger>
                        <SelectContent>
                          {(modelCatalogQuery.data ?? []).map((model) => (
                            <SelectItem key={model.model_id} value={model.model_id}>
                              {model.display_name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    )}
                  />
                  {benchmarkForm.formState.errors.base_model_id ? (
                    <p className="text-sm text-destructive">
                      {benchmarkForm.formState.errors.base_model_id.message}
                    </p>
                  ) : null}
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label>Benchmarks</Label>
                  <BenchmarkPicker
                    selected={benchmarkSelection}
                    onToggle={(benchmark) => toggleSet(setBenchmarkSelection, benchmark)}
                  />
                </div>
                <Button type="submit" className="self-start" disabled={createBenchmark.isPending}>
                  {createBenchmark.isPending ? "Starting..." : "Run benchmark"}
                </Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <div className="mt-6">
        <h2 className="text-lg font-semibold text-foreground">Recent evaluations</h2>
        {evalJobsQuery.isLoading ? (
          <p className="mt-2 text-sm text-muted-foreground">Loading evaluations...</p>
        ) : evalJobsQuery.isError ? (
          <p className="mt-2 text-sm text-destructive">
            {getErrorDetail(evalJobsQuery.error, "Unable to load evaluations.")}
          </p>
        ) : !evalJobsQuery.data || evalJobsQuery.data.length === 0 ? (
          <div className="mt-2 flex flex-col items-center gap-3 rounded-lg border border-dashed border-border py-16 text-center">
            <p className="text-sm text-muted-foreground">No evaluations yet. Start one above.</p>
          </div>
        ) : (
          <Table className="mt-2">
            <TableHeader>
              <TableRow>
                <TableHead>Type</TableHead>
                <TableHead>Model</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Started</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {evalJobsQuery.data.map((job) => (
                <TableRow key={job.id} className="cursor-pointer">
                  <TableCell>
                    <Link href={`/evaluation/${job.id}`} className="font-medium hover:underline">
                      {job.eval_type === "compare" ? "Compare" : "Benchmark"}
                    </Link>
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {job.base_model_id}
                    {job.finetuned_model_id ? ` vs ${job.finetuned_model_id}` : ""}
                  </TableCell>
                  <TableCell>
                    <Badge variant={STATUS_VARIANT[job.status]}>{job.status}</Badge>
                  </TableCell>
                  <TableCell>{new Date(job.created_at).toLocaleString()}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </PageContainer>
  )
}
