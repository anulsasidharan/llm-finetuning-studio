"use client"

import { useParams } from "next/navigation"

import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { PageContainer } from "@/components/layout/PageContainer"
import { FormatSelector } from "@/components/dataset/FormatSelector"
import { QualityReport } from "@/components/dataset/QualityReport"
import { useDataset, useQualityCheckDataset } from "@/hooks/useDatasets"
import { getErrorDetail } from "@/lib/utils"

export default function DatasetDetailPage() {
  const { datasetId } = useParams<{ datasetId: string }>()
  const datasetQuery = useDataset(datasetId)
  const qualityCheckMutation = useQualityCheckDataset(datasetId)

  if (datasetQuery.isLoading) {
    return (
      <PageContainer>
        <p className="text-sm text-muted-foreground">Loading dataset...</p>
      </PageContainer>
    )
  }

  if (datasetQuery.isError || !datasetQuery.data) {
    return (
      <PageContainer>
        <Alert variant="destructive">
          <AlertDescription>
            {getErrorDetail(datasetQuery.error, "Dataset not found.")}
          </AlertDescription>
        </Alert>
      </PageContainer>
    )
  }

  const dataset = datasetQuery.data

  return (
    <PageContainer>
      <h1 className="text-2xl font-semibold text-foreground">{dataset.name}</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        {dataset.row_count} rows · {(dataset.size_bytes / 1024).toFixed(1)} KB · uploaded{" "}
        {new Date(dataset.created_at).toLocaleString()}
      </p>

      <div className="mt-6 flex flex-col gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Format</CardTitle>
          </CardHeader>
          <CardContent>
            <FormatSelector datasetId={dataset.id} format={dataset.format} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quality report</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {qualityCheckMutation.isError ? (
              <Alert variant="destructive">
                <AlertDescription>
                  {getErrorDetail(qualityCheckMutation.error, "Unable to run quality check.")}
                </AlertDescription>
              </Alert>
            ) : null}
            <Button
              type="button"
              variant="outline"
              className="self-start"
              disabled={qualityCheckMutation.isPending}
              onClick={() => qualityCheckMutation.mutate()}
            >
              {qualityCheckMutation.isPending ? "Running..." : "Run quality check"}
            </Button>
            <Separator />
            <QualityReport report={dataset.quality_report ?? null} />
          </CardContent>
        </Card>
      </div>
    </PageContainer>
  )
}
