import { PageContainer } from "@/components/layout/PageContainer"

export default function DashboardPage() {
  return (
    <PageContainer>
      <h1 className="text-2xl font-semibold text-foreground">Dashboard</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Welcome to the LLM Fine-Tuning Studio. Module content lands here in
        later tasks.
      </p>
    </PageContainer>
  )
}
