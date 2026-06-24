import { PageContainer } from "@/components/layout/PageContainer"
import { MethodologyRecommender } from "@/components/training/MethodologyRecommender"

export default function MethodologyPage() {
  return (
    <PageContainer>
      <h1 className="text-2xl font-semibold text-foreground">Methodology selector</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Compare SFT, LoRA, QLoRA, DPO, ORPO, and RLHF, and get a starting-point recommendation
        before building a training config.
      </p>
      <div className="mt-6">
        <MethodologyRecommender />
      </div>
    </PageContainer>
  )
}
