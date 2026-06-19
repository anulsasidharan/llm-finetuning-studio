"use client"

import { Badge } from "@/components/ui/badge"

interface WordCountStats {
  min: number
  max: number
  mean: number
  median: number
}

interface QualityReportData {
  [key: string]: unknown
  total_rows: number
  duplicate_rows: number
  unique_rows: number
  word_count: WordCountStats
  languages: Record<string, number>
}

function isQualityReportData(report: Record<string, unknown>): report is QualityReportData {
  return (
    typeof report.total_rows === "number" &&
    typeof report.duplicate_rows === "number" &&
    typeof report.unique_rows === "number"
  )
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex flex-col gap-1 rounded-lg border border-border bg-card px-3 py-2">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="text-lg font-semibold text-foreground">{value}</span>
    </div>
  )
}

export function QualityReport({ report }: { report: Record<string, unknown> | null }) {
  if (!report || !isQualityReportData(report)) {
    return (
      <p className="text-sm text-muted-foreground">
        No quality report yet. Run a quality check to generate one.
      </p>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatCard label="Total rows" value={report.total_rows} />
        <StatCard label="Unique rows" value={report.unique_rows} />
        <StatCard label="Duplicate rows" value={report.duplicate_rows} />
        <StatCard label="Median words/row" value={report.word_count.median} />
      </div>
      <div className="flex flex-col gap-1.5">
        <span className="text-sm font-medium text-foreground">Languages detected</span>
        <div className="flex flex-wrap gap-1.5">
          {Object.entries(report.languages).map(([language, count]) => (
            <Badge key={language} variant="secondary">
              {language}: {count}
            </Badge>
          ))}
        </div>
      </div>
    </div>
  )
}
