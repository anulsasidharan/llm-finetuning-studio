import { Suspense } from "react"

import { PageContainer } from "@/components/layout/PageContainer"
import { ConfigBuilder } from "@/components/training/ConfigBuilder"

export default function ConfigPage() {
  return (
    <PageContainer>
      <h1 className="text-2xl font-semibold text-foreground">Training config builder</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Choose a methodology, base model, and training parameters to create a fine-tune job.
      </p>
      <div className="mt-6">
        <Suspense fallback={null}>
          <ConfigBuilder />
        </Suspense>
      </div>
    </PageContainer>
  )
}
