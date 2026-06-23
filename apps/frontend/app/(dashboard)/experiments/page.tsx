"use client"

import { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { z } from "zod"

import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { PageContainer } from "@/components/layout/PageContainer"
import { useCreateExperiment, useExperiments } from "@/hooks/useExperiments"
import { getErrorDetail } from "@/lib/utils"

const createExperimentSchema = z.object({
  name: z.string().min(1, "Name is required."),
  description: z.string().optional(),
})

type CreateExperimentFormValues = z.infer<typeof createExperimentSchema>

export default function ExperimentsPage() {
  const router = useRouter()
  const experimentsQuery = useExperiments()
  const createExperiment = useCreateExperiment()
  const [formError, setFormError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CreateExperimentFormValues>({
    resolver: zodResolver(createExperimentSchema),
  })

  async function onSubmit(values: CreateExperimentFormValues) {
    setFormError(null)
    try {
      const experiment = await createExperiment.mutateAsync({
        name: values.name,
        description: values.description || null,
      })
      reset()
      router.push(`/experiments/${experiment.id}`)
    } catch (error) {
      setFormError(getErrorDetail(error, "Unable to create experiment."))
    }
  }

  return (
    <PageContainer>
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Experiments</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Track runs, configs, and metrics across fine-tuning attempts.
        </p>
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>New experiment</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="flex flex-col gap-4" onSubmit={handleSubmit(onSubmit)} noValidate>
            {formError ? (
              <Alert variant="destructive">
                <AlertDescription>{formError}</AlertDescription>
              </Alert>
            ) : null}
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                aria-invalid={Boolean(errors.name)}
                {...register("name")}
              />
              {errors.name ? (
                <p className="text-sm text-destructive">{errors.name.message}</p>
              ) : null}
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="description">Description</Label>
              <Textarea id="description" rows={2} {...register("description")} />
            </div>
            <Button type="submit" className="self-start" disabled={createExperiment.isPending}>
              {createExperiment.isPending ? "Creating..." : "Create experiment"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <div className="mt-6">
        {experimentsQuery.isLoading ? (
          <p className="text-sm text-muted-foreground">Loading experiments...</p>
        ) : experimentsQuery.isError ? (
          <p className="text-sm text-destructive">
            {getErrorDetail(experimentsQuery.error, "Unable to load experiments.")}
          </p>
        ) : !experimentsQuery.data || experimentsQuery.data.length === 0 ? (
          <div className="flex flex-col items-center gap-3 rounded-lg border border-dashed border-border py-16 text-center">
            <p className="text-sm text-muted-foreground">
              No experiments yet. Create one above to start tracking runs.
            </p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Description</TableHead>
                <TableHead>Created</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {experimentsQuery.data.map((experiment) => (
                <TableRow key={experiment.id} className="cursor-pointer">
                  <TableCell>
                    <Link
                      href={`/experiments/${experiment.id}`}
                      className="font-medium hover:underline"
                    >
                      {experiment.name}
                    </Link>
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {experiment.description || "—"}
                  </TableCell>
                  <TableCell>{new Date(experiment.created_at).toLocaleString()}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </PageContainer>
  )
}
