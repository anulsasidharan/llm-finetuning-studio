import { PageContainer } from "@/components/layout/PageContainer"
import { GPUSelector } from "@/components/gpu/GPUSelector"

export default function GPUSelectorPage() {
  return (
    <PageContainer>
      <h1 className="text-2xl font-semibold text-foreground">GPU selector</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Compare GPU instances across AWS, GCP, Azure, RunPod, and Lambda Labs before building a
        training config.
      </p>
      <div className="mt-6">
        <GPUSelector />
      </div>
    </PageContainer>
  )
}
