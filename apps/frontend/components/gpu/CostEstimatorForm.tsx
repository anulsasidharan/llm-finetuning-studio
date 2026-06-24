"use client"

import { useEffect, useMemo } from "react"
import Link from "next/link"
import { useSearchParams } from "next/navigation"
import { zodResolver } from "@hookform/resolvers/zod"
import { Controller, useForm } from "react-hook-form"
import { z } from "zod"

import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { ParameterField } from "@/components/training/ParameterField"
import { METHODOLOGY_INFO } from "@/lib/methodology-data"
import { useDatasets } from "@/hooks/useDatasets"
import { useCostEstimate } from "@/hooks/useCostEstimate"
import { useGPUPricing } from "@/hooks/useGPUPricing"
import { getErrorDetail } from "@/lib/utils"

const METHODOLOGY_VALUES = ["sft", "lora", "qlora", "dpo", "orpo", "rlhf"] as const

const estimatorSchema = z.object({
  vendor: z.string().min(1, "Select a GPU vendor."),
  gpu_type: z.string().min(1, "Select a GPU type."),
  methodology: z.enum(METHODOLOGY_VALUES),
  dataset_id: z.string().optional(),
  dataset_row_count: z.number().int().positive("Must be a positive integer."),
  num_epochs: z.number().int().positive("Must be a positive integer."),
  batch_size: z.number().int().positive("Must be a positive integer."),
  gradient_accumulation_steps: z.number().int().positive("Must be a positive integer."),
})

type EstimatorFormValues = z.infer<typeof estimatorSchema>

const DEFAULT_VALUES: EstimatorFormValues = {
  vendor: "",
  gpu_type: "",
  methodology: "lora",
  dataset_id: "",
  dataset_row_count: 1000,
  num_epochs: 3,
  batch_size: 4,
  gradient_accumulation_steps: 1,
}

function numberFromParam(value: string | null): number | undefined {
  if (!value) return undefined
  const parsed = Number(value)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : undefined
}

export function CostEstimatorForm() {
  const searchParams = useSearchParams()
  const gpuPricingQuery = useGPUPricing()
  const datasetsQuery = useDatasets()
  const estimateMutation = useCostEstimate()

  const instances = useMemo(() => gpuPricingQuery.data ?? [], [gpuPricingQuery.data])
  const vendors = useMemo(
    () => Array.from(new Set(instances.map((instance) => instance.vendor))).sort(),
    [instances]
  )

  const methodologyParam = searchParams.get("methodology")
  const initialMethodology = METHODOLOGY_VALUES.includes(
    methodologyParam as (typeof METHODOLOGY_VALUES)[number]
  )
    ? (methodologyParam as (typeof METHODOLOGY_VALUES)[number])
    : DEFAULT_VALUES.methodology

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    control,
    formState: { errors },
  } = useForm<EstimatorFormValues>({
    resolver: zodResolver(estimatorSchema),
    defaultValues: {
      ...DEFAULT_VALUES,
      methodology: initialMethodology,
      vendor: searchParams.get("cloud_vendor") ?? DEFAULT_VALUES.vendor,
      gpu_type: searchParams.get("gpu_type") ?? DEFAULT_VALUES.gpu_type,
      dataset_id: searchParams.get("dataset_id") ?? DEFAULT_VALUES.dataset_id,
      num_epochs: numberFromParam(searchParams.get("num_epochs")) ?? DEFAULT_VALUES.num_epochs,
      batch_size: numberFromParam(searchParams.get("batch_size")) ?? DEFAULT_VALUES.batch_size,
      gradient_accumulation_steps:
        numberFromParam(searchParams.get("gradient_accumulation_steps")) ??
        DEFAULT_VALUES.gradient_accumulation_steps,
    },
  })

  const vendor = watch("vendor")
  const datasetId = watch("dataset_id")
  const gpuTypeOptions = useMemo(
    () => instances.filter((instance) => instance.vendor === vendor),
    [instances, vendor]
  )

  // Auto-fill (but don't lock) the row count whenever the selected dataset changes.
  useEffect(() => {
    if (!datasetId) return
    const dataset = datasetsQuery.data?.find((item) => item.id === datasetId)
    if (dataset) {
      setValue("dataset_row_count", dataset.row_count, { shouldValidate: true })
    }
  }, [datasetId, datasetsQuery.data, setValue])

  async function onSubmit(values: EstimatorFormValues) {
    await estimateMutation.mutateAsync({
      vendor: values.vendor,
      gpu_type: values.gpu_type,
      methodology: values.methodology,
      num_epochs: values.num_epochs,
      dataset_row_count: values.dataset_row_count,
      batch_size: values.batch_size,
      gradient_accumulation_steps: values.gradient_accumulation_steps,
    })
  }

  return (
    <div className="flex flex-col gap-6">
      <form className="flex flex-col gap-6" onSubmit={handleSubmit(onSubmit)} noValidate>
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between gap-2">
              <CardTitle>GPU instance</CardTitle>
              <Button type="button" variant="outline" size="sm" render={<Link href="/gpu-selector" />}>
                Compare GPUs
              </Button>
            </div>
            <CardDescription>Pick the vendor and GPU type to estimate cost for.</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <ParameterField id="vendor" label="Vendor" error={errors.vendor?.message}>
              <Controller
                control={control}
                name="vendor"
                render={({ field }) => (
                  <Select
                    value={field.value || null}
                    onValueChange={(value) => {
                      field.onChange(value)
                      setValue("gpu_type", "")
                    }}
                  >
                    <SelectTrigger id="vendor" className="w-full">
                      <SelectValue placeholder="Select a vendor" />
                    </SelectTrigger>
                    <SelectContent>
                      {vendors.map((vendorOption) => (
                        <SelectItem key={vendorOption} value={vendorOption}>
                          {vendorOption}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
            </ParameterField>

            <ParameterField id="gpu_type" label="GPU type" error={errors.gpu_type?.message}>
              <Controller
                control={control}
                name="gpu_type"
                render={({ field }) => (
                  <Select value={field.value || null} onValueChange={(value) => field.onChange(value)}>
                    <SelectTrigger id="gpu_type" className="w-full">
                      <SelectValue placeholder="Select a GPU type" />
                    </SelectTrigger>
                    <SelectContent>
                      {gpuTypeOptions.map((instance) => (
                        <SelectItem key={instance.gpu_type} value={instance.gpu_type}>
                          {instance.gpu_type} — ${instance.price_per_hour_usd.toFixed(2)}/hr
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
              {vendor && gpuTypeOptions.length === 0 ? (
                <p className="text-sm text-muted-foreground">No GPU types for this vendor yet.</p>
              ) : null}
            </ParameterField>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Training plan</CardTitle>
            <CardDescription>
              Used to project training duration from your dataset and parameters.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <ParameterField id="methodology" label="Methodology" error={errors.methodology?.message}>
              <Controller
                control={control}
                name="methodology"
                render={({ field }) => (
                  <Select value={field.value} onValueChange={(value) => field.onChange(value)}>
                    <SelectTrigger id="methodology" className="w-full">
                      <SelectValue placeholder="Select a methodology" />
                    </SelectTrigger>
                    <SelectContent>
                      {METHODOLOGY_INFO.map((info) => (
                        <SelectItem key={info.methodology} value={info.methodology}>
                          {info.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
            </ParameterField>

            <ParameterField id="dataset_id" label="Dataset (optional)">
              <Controller
                control={control}
                name="dataset_id"
                render={({ field }) => (
                  <Select value={field.value || ""} onValueChange={(value) => field.onChange(value)}>
                    <SelectTrigger id="dataset_id" className="w-full">
                      <SelectValue placeholder="No dataset selected" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">No dataset</SelectItem>
                      {(datasetsQuery.data ?? []).map((dataset) => (
                        <SelectItem key={dataset.id} value={dataset.id}>
                          {dataset.name} ({dataset.row_count} rows)
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
            </ParameterField>

            <ParameterField
              id="dataset_row_count"
              label="Dataset rows"
              error={errors.dataset_row_count?.message}
            >
              <Input
                id="dataset_row_count"
                type="number"
                {...register("dataset_row_count", { valueAsNumber: true })}
              />
            </ParameterField>

            <ParameterField id="num_epochs" label="Number of epochs" error={errors.num_epochs?.message}>
              <Input id="num_epochs" type="number" {...register("num_epochs", { valueAsNumber: true })} />
            </ParameterField>

            <ParameterField id="batch_size" label="Batch size" error={errors.batch_size?.message}>
              <Input id="batch_size" type="number" {...register("batch_size", { valueAsNumber: true })} />
            </ParameterField>

            <ParameterField
              id="gradient_accumulation_steps"
              label="Gradient accumulation steps"
              error={errors.gradient_accumulation_steps?.message}
            >
              <Input
                id="gradient_accumulation_steps"
                type="number"
                {...register("gradient_accumulation_steps", { valueAsNumber: true })}
              />
            </ParameterField>
          </CardContent>
        </Card>

        {estimateMutation.isError ? (
          <Alert variant="destructive">
            <AlertDescription>
              {getErrorDetail(estimateMutation.error, "Unable to estimate cost.")}
            </AlertDescription>
          </Alert>
        ) : null}

        <Button type="submit" className="self-start" disabled={estimateMutation.isPending}>
          {estimateMutation.isPending ? "Estimating..." : "Estimate cost"}
        </Button>
      </form>

      {estimateMutation.data ? (
        <Card>
          <CardHeader>
            <CardTitle>Pre-flight cost estimate</CardTitle>
            <CardDescription>
              {estimateMutation.data.vendor} {estimateMutation.data.gpu_type} at $
              {estimateMutation.data.price_per_hour_usd.toFixed(2)}/hr
            </CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="flex flex-col gap-1">
              <p className="text-sm text-muted-foreground">Estimated training time</p>
              <p className="text-lg font-semibold">
                {estimateMutation.data.estimated_hours.toFixed(2)} hours
              </p>
            </div>
            <div className="flex flex-col gap-1">
              <p className="text-sm text-muted-foreground">Estimated cost</p>
              <p className="text-lg font-semibold">
                ${estimateMutation.data.estimated_cost_usd.toFixed(2)}
              </p>
            </div>
          </CardContent>
        </Card>
      ) : null}
    </div>
  )
}
