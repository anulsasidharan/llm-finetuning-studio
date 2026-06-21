import Link from "next/link"
import { Database, GitBranch, Rocket, SlidersHorizontal } from "lucide-react"

import { PageContainer } from "@/components/layout/PageContainer"
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

const QUICK_START_ITEMS = [
  {
    href: "/onboarding",
    icon: Rocket,
    title: "Start onboarding",
    description: "Get a guided tour of LoRA, QLoRA, SFT, DPO, ORPO and RLHF before you train.",
  },
  {
    href: "/datasets",
    icon: Database,
    title: "Upload a dataset",
    description: "Bring your data in Alpaca, ShareGPT or ChatML format and run a quality check.",
  },
  {
    href: "/methodology",
    icon: GitBranch,
    title: "Choose a methodology",
    description: "Compare SFT, LoRA, QLoRA, DPO, ORPO and RLHF with an auto-recommendation.",
  },
  {
    href: "/config",
    icon: SlidersHorizontal,
    title: "Build a training config",
    description: "Set hyperparameters with inline guidance, then estimate cost before you launch.",
  },
] as const

export default function DashboardPage() {
  return (
    <PageContainer className="flex flex-col gap-8">
      <div>
        <h1 className="font-heading text-2xl font-semibold text-foreground">
          Welcome back
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
          This is your fine-tuning workspace. Pick up where you left off, or start a new
          run from scratch with one of the steps below.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {QUICK_START_ITEMS.map(({ href, icon: Icon, title, description }) => (
          <Link key={href} href={href} className="group">
            <Card className="h-full transition-colors group-hover:border-primary/40">
              <CardHeader>
                <div className="flex size-9 items-center justify-center rounded-lg bg-accent text-accent-foreground">
                  <Icon className="size-4.5" />
                </div>
                <CardTitle className="mt-2">{title}</CardTitle>
                <CardDescription>{description}</CardDescription>
              </CardHeader>
            </Card>
          </Link>
        ))}
      </div>
    </PageContainer>
  )
}
