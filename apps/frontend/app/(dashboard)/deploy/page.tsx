"use client"

import { useState } from "react"
import { zodResolver } from "@hookform/resolvers/zod"
import { Controller, useForm } from "react-hook-form"
import { z } from "zod"

import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
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
import { PageContainer } from "@/components/layout/PageContainer"
import {
  useCreateRegistryEntry,
  useDeleteRegistryEntry,
  useExportToGGUF,
  usePushToHF,
  useRegistryEntries,
} from "@/hooks/useRegistry"
import { getErrorDetail } from "@/lib/utils"
import type { ExportGGUFRequest, ModelRegistryResponse } from "@/types"

const QUANT_TYPES: ExportGGUFRequest["quantization_type"][] = [
  "q4_k_m",
  "q5_k_m",
  "q8_0",
  "q6_k",
  "q5_0",
  "q4_0",
  "q3_k_m",
  "q2_k",
  "f16",
  "f32",
]

// ── Register model dialog ──────────────────────────────────────────────────

const registerSchema = z.object({
  name: z.string().min(1, "Name is required."),
  base_model_id: z.string().min(1, "Base model is required."),
  storage_path: z.string().optional(),
})
type RegisterFormValues = z.infer<typeof registerSchema>

function RegisterModelDialog() {
  const [open, setOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const createEntry = useCreateRegistryEntry()

  const form = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { name: "", base_model_id: "", storage_path: "" },
  })

  async function onSubmit(values: RegisterFormValues) {
    setError(null)
    try {
      await createEntry.mutateAsync({
        name: values.name,
        base_model_id: values.base_model_id,
        storage_path: values.storage_path || null,
      })
      form.reset()
      setOpen(false)
    } catch (err) {
      setError(getErrorDetail(err, "Unable to register model."))
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger>
        <Button>Register model</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Register a model</DialogTitle>
        </DialogHeader>
        <form
          id="register-model-form"
          className="flex flex-col gap-4 py-2"
          onSubmit={form.handleSubmit(onSubmit)}
          noValidate
        >
          {error ? (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : null}
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="reg-name">Name</Label>
            <Input id="reg-name" placeholder="my-llama3-finetune" {...form.register("name")} />
            {form.formState.errors.name ? (
              <p className="text-sm text-destructive">{form.formState.errors.name.message}</p>
            ) : null}
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="reg-base">Base model ID</Label>
            <Input
              id="reg-base"
              placeholder="meta-llama/Meta-Llama-3-8B"
              {...form.register("base_model_id")}
            />
            {form.formState.errors.base_model_id ? (
              <p className="text-sm text-destructive">
                {form.formState.errors.base_model_id.message}
              </p>
            ) : null}
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="reg-path">Storage path (optional)</Label>
            <Input
              id="reg-path"
              placeholder="fts-models/job-abc123/final"
              {...form.register("storage_path")}
            />
          </div>
        </form>
        <DialogFooter showCloseButton>
          <Button
            type="submit"
            form="register-model-form"
            disabled={createEntry.isPending}
          >
            {createEntry.isPending ? "Registering..." : "Register"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ── Push to HF dialog ─────────────────────────────────────────────────────

const pushHFSchema = z.object({
  hf_repo_id: z.string().min(1, "Repository ID is required."),
  hf_token: z.string().min(1, "HuggingFace token is required."),
  private: z.boolean(),
})
type PushHFFormValues = z.infer<typeof pushHFSchema>

function PushHFDialog({ entry }: { entry: ModelRegistryResponse }) {
  const [open, setOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const pushToHF = usePushToHF()

  const form = useForm<PushHFFormValues>({
    resolver: zodResolver(pushHFSchema),
    defaultValues: {
      hf_repo_id: entry.hf_repo_id ?? `your-org/${entry.name}`,
      hf_token: "",
      private: true,
    },
  })

  async function onSubmit(values: PushHFFormValues) {
    setError(null)
    try {
      await pushToHF.mutateAsync({ entryId: entry.id, payload: values })
      form.reset()
      setOpen(false)
    } catch (err) {
      setError(getErrorDetail(err, "Unable to dispatch push job."))
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger>
        <Button variant="outline" size="sm">
          Push to HF
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Push to HuggingFace Hub</DialogTitle>
        </DialogHeader>
        <form
          id="push-hf-form"
          className="flex flex-col gap-4 py-2"
          onSubmit={form.handleSubmit(onSubmit)}
          noValidate
        >
          {error ? (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : null}
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="hf-repo">Repository ID</Label>
            <Input
              id="hf-repo"
              placeholder="your-org/my-finetuned-model"
              {...form.register("hf_repo_id")}
            />
            {form.formState.errors.hf_repo_id ? (
              <p className="text-sm text-destructive">
                {form.formState.errors.hf_repo_id.message}
              </p>
            ) : null}
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="hf-token">HuggingFace token</Label>
            <Input
              id="hf-token"
              type="password"
              placeholder="hf_..."
              {...form.register("hf_token")}
            />
            {form.formState.errors.hf_token ? (
              <p className="text-sm text-destructive">{form.formState.errors.hf_token.message}</p>
            ) : null}
          </div>
          <div className="flex items-center gap-2">
            <input
              id="hf-private"
              type="checkbox"
              className="h-4 w-4 rounded border-border"
              {...form.register("private")}
            />
            <Label htmlFor="hf-private" className="cursor-pointer font-normal">
              Private repository
            </Label>
          </div>
        </form>
        <DialogFooter showCloseButton>
          <Button type="submit" form="push-hf-form" disabled={pushToHF.isPending}>
            {pushToHF.isPending ? "Dispatching..." : "Push"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ── Export GGUF dialog ────────────────────────────────────────────────────

const exportGGUFSchema = z.object({
  quantization_type: z.enum([
    "f32",
    "f16",
    "q8_0",
    "q6_k",
    "q5_k_m",
    "q5_0",
    "q4_k_m",
    "q4_0",
    "q3_k_m",
    "q2_k",
  ]),
})
type ExportGGUFFormValues = z.infer<typeof exportGGUFSchema>

function ExportGGUFDialog({ entry }: { entry: ModelRegistryResponse }) {
  const [open, setOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const exportToGGUF = useExportToGGUF()

  const form = useForm<ExportGGUFFormValues>({
    resolver: zodResolver(exportGGUFSchema),
    defaultValues: { quantization_type: "q4_k_m" },
  })

  async function onSubmit(values: ExportGGUFFormValues) {
    setError(null)
    try {
      await exportToGGUF.mutateAsync({ entryId: entry.id, payload: values })
      form.reset()
      setOpen(false)
    } catch (err) {
      setError(getErrorDetail(err, "Unable to dispatch GGUF export."))
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger>
        <Button variant="outline" size="sm">
          Export GGUF
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle>Export to GGUF</DialogTitle>
        </DialogHeader>
        <form
          id="export-gguf-form"
          className="flex flex-col gap-4 py-2"
          onSubmit={form.handleSubmit(onSubmit)}
          noValidate
        >
          {error ? (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : null}
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="quant-type">Quantization type</Label>
            <Controller
              control={form.control}
              name="quantization_type"
              render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger id="quant-type" className="w-full">
                    <SelectValue placeholder="Select quantization" />
                  </SelectTrigger>
                  <SelectContent>
                    {QUANT_TYPES.map((qt) => (
                      <SelectItem key={qt} value={qt}>
                        {qt}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
          </div>
        </form>
        <DialogFooter showCloseButton>
          <Button type="submit" form="export-gguf-form" disabled={exportToGGUF.isPending}>
            {exportToGGUF.isPending ? "Dispatching..." : "Export"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ── Delete confirmation dialog ─────────────────────────────────────────────

function DeleteDialog({ entry }: { entry: ModelRegistryResponse }) {
  const [open, setOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const deleteEntry = useDeleteRegistryEntry()

  async function onConfirm() {
    setError(null)
    try {
      await deleteEntry.mutateAsync(entry.id)
      setOpen(false)
    } catch (err) {
      setError(getErrorDetail(err, "Unable to delete entry."))
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger>
        <Button variant="ghost" size="sm" className="text-destructive hover:text-destructive">
          Delete
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle>Delete &ldquo;{entry.name}&rdquo;?</DialogTitle>
        </DialogHeader>
        <p className="text-sm text-muted-foreground">
          This removes the registry entry. The model artifacts in storage are not deleted.
        </p>
        {error ? (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : null}
        <DialogFooter showCloseButton>
          <Button variant="destructive" disabled={deleteEntry.isPending} onClick={onConfirm}>
            {deleteEntry.isPending ? "Deleting..." : "Delete"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ── Export status badges ───────────────────────────────────────────────────

function ExportBadges({ entry }: { entry: ModelRegistryResponse }) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {entry.hf_repo_id ? (
        <Badge variant="default" className="text-xs">
          HF: {entry.hf_repo_id}
        </Badge>
      ) : (
        <Badge variant="outline" className="text-xs text-muted-foreground">
          HF: not pushed
        </Badge>
      )}
      {entry.gguf_export_path ? (
        <Badge variant="default" className="text-xs">
          GGUF: exported
        </Badge>
      ) : (
        <Badge variant="outline" className="text-xs text-muted-foreground">
          GGUF: not exported
        </Badge>
      )}
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────

export default function DeployPage() {
  const registryQuery = useRegistryEntries()

  return (
    <PageContainer>
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Deploy &amp; Export Manager</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Register fine-tuned models, push them to HuggingFace Hub, or export to GGUF for
            local inference.
          </p>
        </div>
        <RegisterModelDialog />
      </div>

      <div className="mt-6">
        {registryQuery.isLoading ? (
          <p className="text-sm text-muted-foreground">Loading registry...</p>
        ) : registryQuery.isError ? (
          <p className="text-sm text-destructive">
            {getErrorDetail(registryQuery.error, "Unable to load model registry.")}
          </p>
        ) : !registryQuery.data || registryQuery.data.length === 0 ? (
          <div className="flex flex-col items-center gap-3 rounded-lg border border-dashed border-border py-20 text-center">
            <p className="text-sm font-medium text-foreground">No models registered yet</p>
            <p className="text-sm text-muted-foreground">
              Register a fine-tuned model above to start exporting and deploying.
            </p>
          </div>
        ) : (
          <Card>
            <CardHeader>
              <CardTitle>Registered models ({registryQuery.data.length})</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Base model</TableHead>
                    <TableHead>Export status</TableHead>
                    <TableHead>Registered</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {registryQuery.data.map((entry) => (
                    <TableRow key={entry.id}>
                      <TableCell className="font-medium">{entry.name}</TableCell>
                      <TableCell className="text-muted-foreground">{entry.base_model_id}</TableCell>
                      <TableCell>
                        <ExportBadges entry={entry} />
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {new Date(entry.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center justify-end gap-1">
                          <PushHFDialog entry={entry} />
                          <ExportGGUFDialog entry={entry} />
                          <DeleteDialog entry={entry} />
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        )}
      </div>
    </PageContainer>
  )
}
