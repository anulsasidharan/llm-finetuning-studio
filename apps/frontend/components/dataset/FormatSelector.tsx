"use client"

import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useFormatDataset } from "@/hooks/useDatasets"
import { getErrorDetail } from "@/lib/utils"
import type { DatasetFormat } from "@/types"

const FORMAT_LABELS: Record<DatasetFormat, string> = {
  alpaca: "Alpaca",
  sharegpt: "ShareGPT",
  chatml: "ChatML",
  unknown: "Unknown",
}

export function FormatSelector({
  datasetId,
  format,
}: {
  datasetId: string
  format: DatasetFormat
}) {
  const formatMutation = useFormatDataset(datasetId)
  const isDetected = format !== "unknown"

  return (
    <div className="flex flex-col gap-3">
      {formatMutation.isError ? (
        <Alert variant="destructive">
          <AlertDescription>
            {getErrorDetail(formatMutation.error, "Unable to detect dataset format.")}
          </AlertDescription>
        </Alert>
      ) : null}
      <div className="flex items-center gap-2">
        <Badge variant={isDetected ? "default" : "outline"}>{FORMAT_LABELS[format]}</Badge>
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={formatMutation.isPending}
          onClick={() => formatMutation.mutate()}
        >
          {formatMutation.isPending
            ? "Detecting..."
            : isDetected
              ? "Re-detect format"
              : "Detect format"}
        </Button>
      </div>
    </div>
  )
}
