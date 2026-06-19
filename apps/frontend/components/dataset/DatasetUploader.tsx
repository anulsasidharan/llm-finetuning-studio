"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"

import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useUploadDataset } from "@/hooks/useDatasets"
import { getErrorDetail } from "@/lib/utils"

const ALLOWED_EXTENSIONS = [".json", ".jsonl"]

function hasAllowedExtension(filename: string): boolean {
  const lowerName = filename.toLowerCase()
  return ALLOWED_EXTENSIONS.some((extension) => lowerName.endsWith(extension))
}

export function DatasetUploader() {
  const router = useRouter()
  const uploadMutation = useUploadDataset()
  const [file, setFile] = useState<File | null>(null)
  const [validationError, setValidationError] = useState<string | null>(null)

  function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files?.[0] ?? null
    setValidationError(
      selected && !hasAllowedExtension(selected.name)
        ? "Dataset file must have a .json or .jsonl extension."
        : null
    )
    setFile(selected)
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    if (!file || validationError) return

    try {
      const dataset = await uploadMutation.mutateAsync(file)
      router.push(`/datasets/${dataset.id}`)
    } catch {
      // Surfaced below via uploadMutation.error
    }
  }

  const errorMessage = uploadMutation.isError
    ? getErrorDetail(uploadMutation.error, "Unable to upload dataset. Please try again.")
    : validationError

  return (
    <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
      {errorMessage ? (
        <Alert variant="destructive">
          <AlertDescription>{errorMessage}</AlertDescription>
        </Alert>
      ) : null}
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="dataset-file">Dataset file</Label>
        <Input
          id="dataset-file"
          type="file"
          accept=".json,.jsonl"
          aria-invalid={Boolean(validationError)}
          onChange={handleFileChange}
        />
        <p className="text-sm text-muted-foreground">
          Accepted formats: .json or .jsonl, up to the configured upload size limit.
        </p>
      </div>
      <Button type="submit" disabled={!file || Boolean(validationError) || uploadMutation.isPending}>
        {uploadMutation.isPending ? "Uploading..." : "Upload dataset"}
      </Button>
    </form>
  )
}
