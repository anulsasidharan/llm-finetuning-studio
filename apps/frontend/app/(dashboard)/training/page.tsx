"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { PageContainer } from "@/components/layout/PageContainer"
import { JobStatusBadge } from "@/components/training/JobStatusBadge"
import { useJobs } from "@/hooks/useJobs"
import { getErrorDetail } from "@/lib/utils"

export default function TrainingPage() {
  const router = useRouter()
  const jobsQuery = useJobs()

  return (
    <PageContainer>
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Training Jobs</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          All fine-tuning jobs — click a row to open the live dashboard.
        </p>
      </div>

      <div className="mt-6">
        {jobsQuery.isLoading ? (
          <p className="text-sm text-muted-foreground">Loading jobs...</p>
        ) : jobsQuery.isError ? (
          <p className="text-sm text-destructive">
            {getErrorDetail(jobsQuery.error, "Unable to load training jobs.")}
          </p>
        ) : !jobsQuery.data || jobsQuery.data.length === 0 ? (
          <div className="flex flex-col items-center gap-3 rounded-lg border border-dashed border-border py-20 text-center">
            <p className="text-sm font-medium text-foreground">No training jobs yet</p>
            <p className="text-sm text-muted-foreground">
              Create a job in the{" "}
              <Link href="/config" className="underline underline-offset-4 hover:text-foreground">
                Config Builder
              </Link>{" "}
              to get started.
            </p>
          </div>
        ) : (
          <Card>
            <CardHeader>
              <CardTitle>Jobs ({jobsQuery.data.length})</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Base model</TableHead>
                    <TableHead>Methodology</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Created</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {jobsQuery.data.map((job) => (
                    <TableRow
                      key={job.id}
                      className="cursor-pointer"
                      onClick={() => router.push(`/training/${job.id}`)}
                    >
                      <TableCell className="font-medium">{job.base_model_id}</TableCell>
                      <TableCell className="uppercase text-muted-foreground">
                        {job.methodology}
                      </TableCell>
                      <TableCell>
                        <JobStatusBadge status={job.status} />
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {new Date(job.created_at).toLocaleString()}
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
