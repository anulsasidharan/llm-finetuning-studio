"use client"

import Link from "next/link"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { PageContainer } from "@/components/layout/PageContainer"
import { useDatasets } from "@/hooks/useDatasets"
import { getErrorDetail } from "@/lib/utils"

export default function DatasetsPage() {
  const datasetsQuery = useDatasets()

  return (
    <PageContainer>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Datasets</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Upload, format, and quality-check the datasets used for fine-tuning.
          </p>
        </div>
        <Button render={<Link href="/datasets/upload" />}>Upload dataset</Button>
      </div>

      <div className="mt-6">
        {datasetsQuery.isLoading ? (
          <p className="text-sm text-muted-foreground">Loading datasets...</p>
        ) : datasetsQuery.isError ? (
          <p className="text-sm text-destructive">
            {getErrorDetail(datasetsQuery.error, "Unable to load datasets.")}
          </p>
        ) : !datasetsQuery.data || datasetsQuery.data.length === 0 ? (
          <div className="flex flex-col items-center gap-3 rounded-lg border border-dashed border-border py-16 text-center">
            <p className="text-sm text-muted-foreground">
              No datasets yet. Upload one to get started.
            </p>
            <Button render={<Link href="/datasets/upload" />}>Upload dataset</Button>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Format</TableHead>
                <TableHead>Rows</TableHead>
                <TableHead>Uploaded</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {datasetsQuery.data.map((dataset) => (
                <TableRow key={dataset.id} className="cursor-pointer">
                  <TableCell>
                    <Link href={`/datasets/${dataset.id}`} className="font-medium hover:underline">
                      {dataset.name}
                    </Link>
                  </TableCell>
                  <TableCell>
                    <Badge variant={dataset.format === "unknown" ? "outline" : "default"}>
                      {dataset.format}
                    </Badge>
                  </TableCell>
                  <TableCell>{dataset.row_count}</TableCell>
                  <TableCell>{new Date(dataset.created_at).toLocaleString()}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </PageContainer>
  )
}
