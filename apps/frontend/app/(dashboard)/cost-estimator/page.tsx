import { Suspense } from "react"

import { PageContainer } from "@/components/layout/PageContainer"
import { CostEstimatorForm } from "@/components/gpu/CostEstimatorForm"

export default function CostEstimatorPage() {
  return (
    <PageContainer>
      <h1 className="text-2xl font-semibold text-foreground">Cost estimator</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Pre-flight cost estimation — project training duration and spend before launching a job.
      </p>
      <div className="mt-6">
        <Suspense fallback={null}>
          <CostEstimatorForm />
        </Suspense>
      </div>
    </PageContainer>
  )
}
