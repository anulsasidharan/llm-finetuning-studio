"use client"

import { useParams } from "next/navigation"

import { Alert, AlertDescription } from "@/components/ui/alert"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { PageContainer } from "@/components/layout/PageContainer"
import { JobStatusBadge } from "@/components/training/JobStatusBadge"
import { TrainingControls } from "@/components/training/TrainingControls"
import { useJob } from "@/hooks/useJobs"
import { getErrorDetail } from "@/lib/utils"

export default function JobDetailPage() {
  const { jobId } = useParams<{ jobId: string }>()
  const jobQuery = useJob(jobId)

  if (jobQuery.isLoading) {
    return (
      <PageContainer>
        <p className="text-sm text-muted-foreground">Loading job...</p>
      </PageContainer>
    )
  }

  if (jobQuery.isError || !jobQuery.data) {
    return (
      <PageContainer>
        <Alert variant="destructive">
          <AlertDescription>{getErrorDetail(jobQuery.error, "Job not found.")}</AlertDescription>
        </Alert>
      </PageContainer>
    )
  }

  const job = jobQuery.data

  return (
    <PageContainer>
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-semibold text-foreground">{job.base_model_id}</h1>
        <JobStatusBadge status={job.status} />
      </div>
      <p className="mt-1 text-sm text-muted-foreground">
        {job.methodology.toUpperCase()} · created {new Date(job.created_at).toLocaleString()}
      </p>

      <div className="mt-6 flex flex-col gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Controls</CardTitle>
          </CardHeader>
          <CardContent>
            <TrainingControls status={job.status} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Training config</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="overflow-x-auto rounded-md bg-muted p-4 text-sm">
              {JSON.stringify(job.training_config, null, 2)}
            </pre>
          </CardContent>
        </Card>
      </div>
    </PageContainer>
  )
}
