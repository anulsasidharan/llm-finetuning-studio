"use client"

import { useState } from "react"
import Link from "next/link"
import { useRouter, useSearchParams } from "next/navigation"
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
import { Separator } from "@/components/ui/separator"
import { MethodologyCard, METHODOLOGY_INFO } from "@/components/training/MethodologyCard"
import { ParameterField } from "@/components/training/ParameterField"
import { PARAMETER_INFO } from "@/components/training/ParameterTooltip"
import { useDatasets } from "@/hooks/useDatasets"
import { useCreateJob } from "@/hooks/useJobs"
import { useModelCatalog } from "@/hooks/useModelCatalog"
import { getErrorDetail } from "@/lib/utils"

const METHODOLOGY_VALUES = ["sft", "lora", "qlora", "dpo", "orpo", "rlhf"] as const

const configSchema = z
  .object({
    base_model_id: z.string().min(1, "Select a base model."),
    methodology: z.enum(METHODOLOGY_VALUES),
    dataset_id: z.string().optional(),
    gpu_type: z.string().optional(),
    cloud_vendor: z.string().optional(),
    learning_rate: z.number().positive("Must be greater than 0."),
    num_epochs: z.number().int().positive("Must be a positive integer."),
    batch_size: z.number().int().positive("Must be a positive integer."),
    warmup_ratio: z.number().min(0).max(1, "Must be between 0 and 1."),
    weight_decay: z.number().min(0, "Cannot be negative."),
    max_seq_length: z.number().int().positive("Must be a positive integer."),
    gradient_accumulation_steps: z.number().int().positive("Must be a positive integer."),
    lora_r: z.number().int().positive("Must be a positive integer.").optional(),
    lora_alpha: z.number().int().positive("Must be a positive integer.").optional(),
    beta: z.number().optional(),
    reward_model_id: z.string().optional(),
  })
  .superRefine((values, ctx) => {
    if (values.methodology === "lora" || values.methodology === "qlora") {
      if (values.lora_r === undefined) {
        ctx.addIssue({
          path: ["lora_r"],
          code: z.ZodIssueCode.custom,
          message: "Required for LoRA/QLoRA.",
        })
      }
      if (values.lora_alpha === undefined) {
        ctx.addIssue({
          path: ["lora_alpha"],
          code: z.ZodIssueCode.custom,
          message: "Required for LoRA/QLoRA.",
        })
      }
    }
    if (values.methodology === "dpo" || values.methodology === "orpo") {
      if (values.beta === undefined) {
        ctx.addIssue({
          path: ["beta"],
          code: z.ZodIssueCode.custom,
          message: "Required for DPO/ORPO.",
        })
      }
    }
    if (values.methodology === "rlhf" && !values.reward_model_id) {
      ctx.addIssue({
        path: ["reward_model_id"],
        code: z.ZodIssueCode.custom,
        message: "Required for RLHF.",
      })
    }
  })

type ConfigFormValues = z.infer<typeof configSchema>

const DEFAULT_VALUES: ConfigFormValues = {
  base_model_id: "",
  methodology: "lora",
  dataset_id: "",
  gpu_type: "",
  cloud_vendor: "",
  learning_rate: 0.0002,
  num_epochs: 3,
  batch_size: 4,
  warmup_ratio: 0.03,
  weight_decay: 0,
  max_seq_length: 2048,
  gradient_accumulation_steps: 1,
  lora_r: 8,
  lora_alpha: 16,
  beta: 0.1,
  reward_model_id: "",
}

function buildTrainingConfig(values: ConfigFormValues): Record<string, unknown> {
  const config: Record<string, unknown> = {
    learning_rate: values.learning_rate,
    num_epochs: values.num_epochs,
    batch_size: values.batch_size,
    warmup_ratio: values.warmup_ratio,
    weight_decay: values.weight_decay,
    max_seq_length: values.max_seq_length,
    gradient_accumulation_steps: values.gradient_accumulation_steps,
  }
  if (values.methodology === "lora" || values.methodology === "qlora") {
    config.lora_r = values.lora_r
    config.lora_alpha = values.lora_alpha
  }
  if (values.methodology === "dpo" || values.methodology === "orpo") {
    config.beta = values.beta
  }
  if (values.methodology === "rlhf") {
    config.reward_model_id = values.reward_model_id
  }
  return config
}

export function ConfigBuilder() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const modelCatalogQuery = useModelCatalog()
  const datasetsQuery = useDatasets()
  const createJobMutation = useCreateJob()
  const [formError, setFormError] = useState<string | null>(null)

  const methodologyParam = searchParams.get("methodology")
  const initialMethodology = METHODOLOGY_VALUES.includes(
    methodologyParam as (typeof METHODOLOGY_VALUES)[number]
  )
    ? (methodologyParam as (typeof METHODOLOGY_VALUES)[number])
    : DEFAULT_VALUES.methodology

  const initialGpuType = searchParams.get("gpu_type") ?? DEFAULT_VALUES.gpu_type
  const initialCloudVendor = searchParams.get("cloud_vendor") ?? DEFAULT_VALUES.cloud_vendor

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    control,
    formState: { errors },
  } = useForm<ConfigFormValues>({
    resolver: zodResolver(configSchema),
    defaultValues: {
      ...DEFAULT_VALUES,
      methodology: initialMethodology,
      gpu_type: initialGpuType,
      cloud_vendor: initialCloudVendor,
    },
  })

  const methodology = watch("methodology")

  async function onSubmit(values: ConfigFormValues) {
    setFormError(null)
    try {
      const job = await createJobMutation.mutateAsync({
        base_model_id: values.base_model_id,
        methodology: values.methodology,
        training_config: buildTrainingConfig(values),
        dataset_id: values.dataset_id ? values.dataset_id : null,
        gpu_type: values.gpu_type ? values.gpu_type : null,
        cloud_vendor: values.cloud_vendor ? values.cloud_vendor : null,
      })
      router.push(`/config/${job.id}`)
    } catch (error) {
      setFormError(getErrorDetail(error, "Unable to create the fine-tune job."))
    }
  }

  return (
    <form className="flex flex-col gap-6" onSubmit={handleSubmit(onSubmit)} noValidate>
      {formError ? (
        <Alert variant="destructive">
          <AlertDescription>{formError}</AlertDescription>
        </Alert>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Methodology</CardTitle>
          <CardDescription>Choose the fine-tuning approach for this job.</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {METHODOLOGY_INFO.map((info) => (
            <MethodologyCard
              key={info.methodology}
              info={info}
              selected={methodology === info.methodology}
              onSelect={() => setValue("methodology", info.methodology, { shouldValidate: true })}
            />
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Model &amp; dataset</CardTitle>
          <CardDescription>Pick the base model to fine-tune and the dataset to use.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <ParameterField
            id="base_model_id"
            label="Base model"
            error={errors.base_model_id?.message}
          >
            <Controller
              control={control}
              name="base_model_id"
              render={({ field }) => (
                <Select value={field.value || null} onValueChange={(value) => field.onChange(value)}>
                  <SelectTrigger id="base_model_id" className="w-full">
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
            {modelCatalogQuery.isLoading ? (
              <p className="text-sm text-muted-foreground">Loading model catalog...</p>
            ) : null}
            {modelCatalogQuery.isSuccess && modelCatalogQuery.data.length === 0 ? (
              <p className="text-sm text-muted-foreground">No models in the catalog yet.</p>
            ) : null}
          </ParameterField>

          <ParameterField id="dataset_id" label="Dataset (optional)">
            <Controller
              control={control}
              name="dataset_id"
              render={({ field }) => (
                <Select
                  value={field.value || ""}
                  onValueChange={(value) => field.onChange(value)}
                >
                  <SelectTrigger id="dataset_id" className="w-full">
                    <SelectValue placeholder="No dataset selected" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">No dataset</SelectItem>
                    {(datasetsQuery.data ?? []).map((dataset) => (
                      <SelectItem key={dataset.id} value={dataset.id}>
                        {dataset.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
          </ParameterField>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Training parameters</CardTitle>
          <CardDescription>Common parameters required for every methodology.</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <ParameterField
            id="learning_rate"
            label="Learning rate"
            error={errors.learning_rate?.message}
            info={PARAMETER_INFO.learning_rate}
          >
            <Input
              id="learning_rate"
              type="number"
              step="any"
              {...register("learning_rate", { valueAsNumber: true })}
            />
          </ParameterField>
          <ParameterField
            id="num_epochs"
            label="Number of epochs"
            error={errors.num_epochs?.message}
            info={PARAMETER_INFO.num_epochs}
          >
            <Input
              id="num_epochs"
              type="number"
              {...register("num_epochs", { valueAsNumber: true })}
            />
          </ParameterField>
          <ParameterField
            id="batch_size"
            label="Batch size"
            error={errors.batch_size?.message}
            info={PARAMETER_INFO.batch_size}
          >
            <Input
              id="batch_size"
              type="number"
              {...register("batch_size", { valueAsNumber: true })}
            />
          </ParameterField>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Additional parameters</CardTitle>
          <CardDescription>
            Extra parameters commonly used across methodologies (not yet enforced by the
            backend).
          </CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <ParameterField
            id="warmup_ratio"
            label="Warmup ratio"
            error={errors.warmup_ratio?.message}
            info={PARAMETER_INFO.warmup_ratio}
          >
            <Input
              id="warmup_ratio"
              type="number"
              step="any"
              {...register("warmup_ratio", { valueAsNumber: true })}
            />
          </ParameterField>
          <ParameterField
            id="weight_decay"
            label="Weight decay"
            error={errors.weight_decay?.message}
            info={PARAMETER_INFO.weight_decay}
          >
            <Input
              id="weight_decay"
              type="number"
              step="any"
              {...register("weight_decay", { valueAsNumber: true })}
            />
          </ParameterField>
          <ParameterField
            id="max_seq_length"
            label="Max sequence length"
            error={errors.max_seq_length?.message}
            info={PARAMETER_INFO.max_seq_length}
          >
            <Input
              id="max_seq_length"
              type="number"
              {...register("max_seq_length", { valueAsNumber: true })}
            />
          </ParameterField>
          <ParameterField
            id="gradient_accumulation_steps"
            label="Gradient accumulation steps"
            error={errors.gradient_accumulation_steps?.message}
            info={PARAMETER_INFO.gradient_accumulation_steps}
          >
            <Input
              id="gradient_accumulation_steps"
              type="number"
              {...register("gradient_accumulation_steps", { valueAsNumber: true })}
            />
          </ParameterField>
        </CardContent>
      </Card>

      {methodology === "lora" || methodology === "qlora" ? (
        <Card>
          <CardHeader>
            <CardTitle>LoRA parameters</CardTitle>
            <CardDescription>Required for LoRA and QLoRA.</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <ParameterField
              id="lora_r"
              label="LoRA rank (r)"
              error={errors.lora_r?.message}
              info={PARAMETER_INFO.lora_r}
            >
              <Input
                id="lora_r"
                type="number"
                {...register("lora_r", { valueAsNumber: true })}
              />
            </ParameterField>
            <ParameterField
              id="lora_alpha"
              label="LoRA alpha"
              error={errors.lora_alpha?.message}
              info={PARAMETER_INFO.lora_alpha}
            >
              <Input
                id="lora_alpha"
                type="number"
                {...register("lora_alpha", { valueAsNumber: true })}
              />
            </ParameterField>
          </CardContent>
        </Card>
      ) : null}

      {methodology === "dpo" || methodology === "orpo" ? (
        <Card>
          <CardHeader>
            <CardTitle>Alignment parameters</CardTitle>
            <CardDescription>Required for DPO and ORPO.</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <ParameterField id="beta" label="Beta" error={errors.beta?.message} info={PARAMETER_INFO.beta}>
              <Input id="beta" type="number" step="any" {...register("beta", { valueAsNumber: true })} />
            </ParameterField>
          </CardContent>
        </Card>
      ) : null}

      {methodology === "rlhf" ? (
        <Card>
          <CardHeader>
            <CardTitle>RLHF parameters</CardTitle>
            <CardDescription>Required for RLHF.</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <ParameterField
              id="reward_model_id"
              label="Reward model ID"
              error={errors.reward_model_id?.message}
              info={PARAMETER_INFO.reward_model_id}
            >
              <Input id="reward_model_id" type="text" {...register("reward_model_id")} />
            </ParameterField>
          </CardContent>
        </Card>
      ) : null}

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between gap-2">
            <CardTitle>Compute (optional)</CardTitle>
            <Button type="button" variant="outline" size="sm" render={<Link href="/gpu-selector" />}>
              Compare GPUs
            </Button>
          </div>
          <CardDescription>
            Leave blank to decide later, or compare GPU instances across vendors first.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <ParameterField id="gpu_type" label="GPU type">
            <Input id="gpu_type" type="text" placeholder="e.g. A100-80GB" {...register("gpu_type")} />
          </ParameterField>
          <ParameterField id="cloud_vendor" label="Cloud vendor">
            <Input
              id="cloud_vendor"
              type="text"
              placeholder="e.g. AWS"
              {...register("cloud_vendor")}
            />
          </ParameterField>
        </CardContent>
      </Card>

      <Separator />

      <Button type="submit" className="self-start" disabled={createJobMutation.isPending}>
        {createJobMutation.isPending ? "Creating job..." : "Create job"}
      </Button>
    </form>
  )
}
