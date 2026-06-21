import Link from "next/link"
import {
  ArrowRight,
  Calculator,
  Cpu,
  Database,
  FlaskConical,
  GitBranch,
  Rocket,
  SlidersHorizontal,
  Activity,
  UploadCloud,
  type LucideIcon,
} from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { METHODOLOGY_INFO } from "@/lib/methodology-data"

import { MarketingFooter } from "./_components/MarketingFooter"
import { MarketingNav } from "./_components/MarketingNav"

const STATS = [
  { value: "6", label: "Fine-tuning methodologies" },
  { value: "5", label: "Cloud GPU vendors" },
  { value: "3", label: "Dataset formats supported" },
  { value: "1", label: "Platform, start to deploy" },
] as const

const FEATURES: { icon: LucideIcon; title: string; description: string }[] = [
  {
    icon: Database,
    title: "Dataset Studio",
    description: "Upload, format, and quality-check datasets in Alpaca, ShareGPT, or ChatML.",
  },
  {
    icon: GitBranch,
    title: "Methodology Selector",
    description: "Compare SFT, LoRA, QLoRA, DPO, ORPO, and RLHF with an auto-recommendation.",
  },
  {
    icon: SlidersHorizontal,
    title: "Training Config Builder",
    description: "A full parameter panel with inline contextual education for every field.",
  },
  {
    icon: Cpu,
    title: "Multi-cloud GPU Selector",
    description: "Compare and launch training across AWS, GCP, Azure, RunPod, and Lambda Labs.",
  },
  {
    icon: Calculator,
    title: "Cost Forecaster",
    description: "Pre-flight cost estimation so you know the bill before any job runs.",
  },
  {
    icon: Activity,
    title: "Live Training Dashboard",
    description: "Real-time loss curves, GPU utilization, and ETA over a live WebSocket feed.",
  },
  {
    icon: FlaskConical,
    title: "Evaluation Playground",
    description: "Side-by-side base vs. fine-tuned model comparison against benchmarks.",
  },
  {
    icon: UploadCloud,
    title: "Deploy & Export",
    description: "Push to GGUF, the HuggingFace Hub, vLLM, or a generated REST endpoint.",
  },
]

const HOW_IT_WORKS = [
  {
    step: "01",
    title: "Upload & format",
    description: "Bring a dataset, pick a format, and run an automated quality check.",
  },
  {
    step: "02",
    title: "Choose & configure",
    description: "Select a methodology, tune parameters, and pick GPU hardware and vendor.",
  },
  {
    step: "03",
    title: "Train & monitor",
    description: "Launch the job and watch loss curves, VRAM, and throughput live.",
  },
  {
    step: "04",
    title: "Evaluate & deploy",
    description: "Benchmark against the base model, then export or deploy in one step.",
  },
] as const

export default function MarketingPage() {
  return (
    <>
      <MarketingNav />

      <main className="flex-1">
        {/* Hero */}
        <section className="relative overflow-hidden border-b border-border">
          <div
            aria-hidden
            className="absolute inset-0 -z-10 bg-[image:radial-gradient(circle_at_top,var(--color-indigo-100),transparent_60%)] dark:bg-[image:radial-gradient(circle_at_top,var(--color-indigo-950),transparent_60%)]"
          />
          <div className="mx-auto grid w-full max-w-6xl items-center gap-12 px-4 py-20 sm:px-6 lg:grid-cols-2 lg:px-8 lg:py-28">
            <div>
              <Badge variant="secondary" className="mb-5">
                Phase 1 &middot; In active development
              </Badge>
              <h1 className="font-heading text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">
                Fine-tune LLMs from zero knowledge to a deployed model.
              </h1>
              <p className="mt-5 max-w-xl text-base text-muted-foreground sm:text-lg">
                One end-to-end studio for dataset prep, methodology selection, training
                configuration, multi-cloud GPU launch, live monitoring, evaluation, and
                deployment &mdash; without stitching together five different tools.
              </p>
              <div className="mt-8 flex flex-wrap items-center gap-3">
                <Button size="lg" nativeButton={false} render={<Link href="/register" />}>
                  Get started
                  <ArrowRight className="size-4" />
                </Button>
                <Button
                  size="lg"
                  variant="outline"
                  nativeButton={false}
                  render={<Link href="/onboarding" />}
                >
                  See how it works
                </Button>
              </div>
            </div>

            <Card className="ring-foreground/10 shadow-xl shadow-indigo-500/5">
              <CardHeader className="gap-4 border-b border-border pb-4">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm">qlora-llama3-8b-run-04</CardTitle>
                  <Badge variant="secondary">Training</Badge>
                </div>
                <CardDescription>QLoRA &middot; A100 80GB &middot; RunPod</CardDescription>
              </CardHeader>
              <div className="flex flex-col gap-4 px-(--card-spacing) pt-4">
                {[
                  { label: "Train loss", value: "0.42" },
                  { label: "GPU utilization", value: "97%" },
                  { label: "Est. cost", value: "$3.18" },
                ].map((row) => (
                  <div key={row.label} className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">{row.label}</span>
                    <span className="font-mono font-medium text-foreground">{row.value}</span>
                  </div>
                ))}
                <div className="h-20 rounded-lg bg-gradient-to-r from-indigo-500/15 via-violet-500/15 to-indigo-500/5" />
              </div>
            </Card>
          </div>
        </section>

        {/* Stats */}
        <section className="border-b border-border bg-muted/40">
          <div className="mx-auto grid w-full max-w-6xl grid-cols-2 gap-8 px-4 py-12 sm:px-6 md:grid-cols-4 lg:px-8">
            {STATS.map((stat) => (
              <div key={stat.label} className="text-center sm:text-left">
                <p className="font-heading text-3xl font-semibold text-foreground">{stat.value}</p>
                <p className="mt-1 text-sm text-muted-foreground">{stat.label}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Features */}
        <section id="features" className="mx-auto w-full max-w-6xl px-4 py-20 sm:px-6 lg:px-8">
          <div className="max-w-2xl">
            <h2 className="font-heading text-3xl font-semibold text-foreground">
              Every step of the fine-tuning lifecycle, in one place
            </h2>
            <p className="mt-3 text-muted-foreground">
              No more juggling notebooks, spreadsheets, and ad hoc scripts across five tools.
            </p>
          </div>

          <div className="mt-10 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {FEATURES.map(({ icon: Icon, title, description }) => (
              <Card key={title} className="transition-colors hover:border-primary/40">
                <CardHeader>
                  <div className="flex size-9 items-center justify-center rounded-lg bg-accent text-accent-foreground">
                    <Icon className="size-4.5" />
                  </div>
                  <CardTitle className="mt-2">{title}</CardTitle>
                  <CardDescription>{description}</CardDescription>
                </CardHeader>
              </Card>
            ))}
          </div>
        </section>

        {/* How it works */}
        <section id="how-it-works" className="border-y border-border bg-muted/40">
          <div className="mx-auto w-full max-w-6xl px-4 py-20 sm:px-6 lg:px-8">
            <div className="max-w-2xl">
              <h2 className="font-heading text-3xl font-semibold text-foreground">
                From raw data to a deployed endpoint
              </h2>
              <p className="mt-3 text-muted-foreground">
                A guided, four-step flow built for people who have never fine-tuned a model
                before &mdash; and powerful enough for people who have.
              </p>
            </div>

            <div className="mt-10 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {HOW_IT_WORKS.map((item) => (
                <div key={item.step}>
                  <span className="font-heading text-sm font-semibold text-primary">
                    {item.step}
                  </span>
                  <h3 className="mt-2 font-heading text-lg font-semibold text-foreground">
                    {item.title}
                  </h3>
                  <p className="mt-2 text-sm text-muted-foreground">{item.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Methodology comparison teaser */}
        <section id="methodologies" className="mx-auto w-full max-w-6xl px-4 py-20 sm:px-6 lg:px-8">
          <div className="max-w-2xl">
            <h2 className="font-heading text-3xl font-semibold text-foreground">
              Pick the right methodology, with the trade-offs spelled out
            </h2>
            <p className="mt-3 text-muted-foreground">
              SFT, LoRA, QLoRA, DPO, ORPO, and RLHF &mdash; compared side by side so you don&apos;t
              have to read six papers first.
            </p>
          </div>

          <div className="mt-10 overflow-x-auto rounded-xl border border-border">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead className="bg-muted/60 text-muted-foreground">
                <tr>
                  <th className="px-4 py-3 font-medium">Method</th>
                  <th className="px-4 py-3 font-medium">VRAM usage</th>
                  <th className="px-4 py-3 font-medium">Min samples</th>
                  <th className="px-4 py-3 font-medium">Key differentiator</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {METHODOLOGY_INFO.map((info) => (
                  <tr key={info.methodology}>
                    <td className="px-4 py-3 font-medium text-foreground">{info.label}</td>
                    <td className="px-4 py-3 text-muted-foreground">{info.vramUsage}</td>
                    <td className="px-4 py-3 text-muted-foreground">{info.minSamples}</td>
                    <td className="px-4 py-3 text-muted-foreground">{info.keyDifferentiator}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Final CTA */}
        <section className="border-t border-border bg-gradient-to-br from-indigo-600 to-violet-600">
          <div className="mx-auto flex w-full max-w-6xl flex-col items-start gap-6 px-4 py-16 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8">
            <div>
              <h2 className="font-heading text-3xl font-semibold text-white">
                Ready to fine-tune your first model?
              </h2>
              <p className="mt-2 max-w-xl text-indigo-100">
                Create an account and start with the guided onboarding wizard.
              </p>
            </div>
            <Button
              size="lg"
              variant="secondary"
              className="shrink-0 bg-white text-indigo-700 hover:bg-indigo-50"
              nativeButton={false}
              render={<Link href="/register" />}
            >
              <Rocket className="size-4" />
              Get started for free
            </Button>
          </div>
        </section>
      </main>

      <MarketingFooter />
    </>
  )
}
