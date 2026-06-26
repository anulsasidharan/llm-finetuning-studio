"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import {
  ArrowLeft,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  ChevronRight,
  Cpu,
  Database,
  FlaskConical,
  GitBranch,
  GraduationCap,
  Layers,
  Rocket,
  SlidersHorizontal,
  Zap,
} from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { PageContainer } from "@/components/layout/PageContainer"
import { METHODOLOGY_INFO, type MethodologyInfo } from "@/lib/methodology-data"
import type { Methodology } from "@/types"
import { cn } from "@/lib/utils"

// ── Types ──────────────────────────────────────────────────────────────────

type ExperienceLevel = "beginner" | "advanced"

// ── Methodology display (sourced from lib/methodology-data.ts) ─────────────

const METHODOLOGY_COLORS: Record<Methodology, string> = {
  sft: "bg-blue-500/10 border-blue-500/30 text-blue-700 dark:text-blue-400",
  lora: "bg-violet-500/10 border-violet-500/30 text-violet-700 dark:text-violet-400",
  qlora: "bg-emerald-500/10 border-emerald-500/30 text-emerald-700 dark:text-emerald-400",
  dpo: "bg-orange-500/10 border-orange-500/30 text-orange-700 dark:text-orange-400",
  orpo: "bg-pink-500/10 border-pink-500/30 text-pink-700 dark:text-pink-400",
  rlhf: "bg-amber-500/10 border-amber-500/30 text-amber-700 dark:text-amber-400",
}

const METHODOLOGY_TITLES: Record<Methodology, string> = {
  sft: "SFT — Supervised Fine-Tuning",
  lora: "LoRA — Low-Rank Adaptation",
  qlora: "QLoRA — Quantized LoRA",
  dpo: "DPO — Direct Preference Optimisation",
  orpo: "ORPO — Odds Ratio Preference Optimisation",
  rlhf: "RLHF — Reinforcement Learning from Human Feedback",
}

const METHODOLOGY_VRAM_LABELS: Record<Methodology, string> = {
  sft: "Full model VRAM",
  lora: "~40% of SFT",
  qlora: "~15% of SFT",
  dpo: "~2× LoRA",
  orpo: "~LoRA",
  rlhf: "~4× base",
}

const STUDIO_MODULES = [
  { icon: Database, label: "Datasets", href: "/datasets", desc: "Upload, format & quality-check your training data" },
  { icon: GitBranch, label: "Methodology", href: "/methodology", desc: "Pick the right fine-tuning strategy for your goal" },
  { icon: SlidersHorizontal, label: "Config Builder", href: "/config", desc: "Set hyperparameters with inline explanations" },
  { icon: Cpu, label: "GPU Selector", href: "/gpu-selector", desc: "Compare cloud GPUs and pick what fits your budget" },
  { icon: FlaskConical, label: "Training", href: "/training", desc: "Launch jobs and watch live loss curves" },
  { icon: Zap, label: "Evaluation", href: "/evaluation", desc: "Benchmark and compare base vs fine-tuned" },
  { icon: Rocket, label: "Deploy", href: "/deploy", desc: "Export to GGUF or push to HuggingFace Hub" },
]

// ── Step definitions ───────────────────────────────────────────────────────

const BEGINNER_STEPS = ["experience", "what-is-ft", "methods", "resources", "tour", "done"] as const
const ADVANCED_STEPS = ["experience", "methods", "tour", "done"] as const

type BeginnerStep = (typeof BEGINNER_STEPS)[number]
type AdvancedStep = (typeof ADVANCED_STEPS)[number]
type WizardStep = BeginnerStep | AdvancedStep

// ── Sub-components ─────────────────────────────────────────────────────────

function StepProgress({ current, total }: { current: number; total: number }) {
  const pct = Math.round((current / (total - 1)) * 100)
  return (
    <div className="mb-8 flex flex-col gap-2">
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>
          Step {current + 1} of {total}
        </span>
        <span>{pct}% complete</span>
      </div>
      <Progress value={pct} />
    </div>
  )
}

function MethodCard({ info }: { info: MethodologyInfo }) {
  const color = METHODOLOGY_COLORS[info.methodology]
  return (
    <Card className={cn("border", color.split(" ").slice(0, 2).join(" "))}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between gap-2">
          <CardTitle className="text-sm font-semibold">
            {METHODOLOGY_TITLES[info.methodology]}
          </CardTitle>
          <Badge variant="outline" className="shrink-0 text-xs uppercase">
            {info.label}
          </Badge>
        </div>
        <CardDescription className="text-xs">{info.keyDifferentiator}</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-1.5 text-xs text-muted-foreground">
        <div className="flex gap-1">
          <span className="font-medium text-foreground">VRAM:</span>
          {METHODOLOGY_VRAM_LABELS[info.methodology]}
        </div>
        <div className="flex gap-1">
          <span className="font-medium text-foreground">Min samples:</span>
          {info.minSamples}
        </div>
        <div className="flex gap-1">
          <span className="font-medium text-foreground">Trainer:</span>
          {info.trainerClass}
        </div>
      </CardContent>
    </Card>
  )
}

// ── Step screens ───────────────────────────────────────────────────────────

function ExperienceStep({ onSelect }: { onSelect: (level: ExperienceLevel) => void }) {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-xl font-semibold">Welcome to Fine-Tuning Studio</h2>
        <p className="mt-1.5 text-sm text-muted-foreground">
          Tell us where you&apos;re starting from so we can tailor the walkthrough.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <button
          type="button"
          onClick={() => onSelect("beginner")}
          className="group flex flex-col gap-3 rounded-xl border border-border bg-card p-6 text-left transition-colors hover:border-primary hover:bg-primary/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <div className="flex size-10 items-center justify-center rounded-lg bg-primary/10">
            <BookOpen className="size-5 text-primary" />
          </div>
          <div>
            <p className="font-semibold text-foreground">New to fine-tuning</p>
            <p className="mt-0.5 text-sm text-muted-foreground">
              Start with the concepts — what fine-tuning is, how the methods differ, and what
              resources you need.
            </p>
          </div>
          <div className="mt-auto flex items-center gap-1 text-xs text-primary">
            Full walkthrough
            <ChevronRight className="size-3.5" />
          </div>
        </button>

        <button
          type="button"
          onClick={() => onSelect("advanced")}
          className="group flex flex-col gap-3 rounded-xl border border-border bg-card p-6 text-left transition-colors hover:border-primary hover:bg-primary/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <div className="flex size-10 items-center justify-center rounded-lg bg-primary/10">
            <GraduationCap className="size-5 text-primary" />
          </div>
          <div>
            <p className="font-semibold text-foreground">I know the basics</p>
            <p className="mt-0.5 text-sm text-muted-foreground">
              Skip the theory. Just show me the method reference and how this studio is laid out.
            </p>
          </div>
          <div className="mt-auto flex items-center gap-1 text-xs text-primary">
            Quick tour
            <ChevronRight className="size-3.5" />
          </div>
        </button>
      </div>
    </div>
  )
}

function WhatIsFineTuningStep() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-xl font-semibold">What is fine-tuning?</h2>
        <p className="mt-1.5 text-sm text-muted-foreground">
          A quick mental model before you touch any settings.
        </p>
      </div>

      <Card>
        <CardContent className="flex flex-col gap-4 pt-6">
          <div className="flex gap-4">
            <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-sm font-bold text-primary">
              1
            </div>
            <div>
              <p className="font-medium">Pre-trained = general knowledge</p>
              <p className="mt-0.5 text-sm text-muted-foreground">
                A base model (like Llama-3 or Mistral) is trained on trillions of tokens from the
                internet. It knows a lot — but it doesn&apos;t know your domain, your format, or
                your preferred style.
              </p>
            </div>
          </div>

          <Separator />

          <div className="flex gap-4">
            <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-sm font-bold text-primary">
              2
            </div>
            <div>
              <p className="font-medium">Fine-tuning = specialisation</p>
              <p className="mt-0.5 text-sm text-muted-foreground">
                You show the model examples of exactly the task you want — customer support
                replies, code completions, medical summaries. The model updates its weights to get
                better at your specific task without forgetting general knowledge.
              </p>
            </div>
          </div>

          <Separator />

          <div className="flex gap-4">
            <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-sm font-bold text-primary">
              3
            </div>
            <div>
              <p className="font-medium">The result = your model</p>
              <p className="mt-0.5 text-sm text-muted-foreground">
                After training, you get a model (or a small adapter file) that you can deploy,
                share on HuggingFace Hub, or export to a portable GGUF file for local inference.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="border-amber-500/30 bg-amber-500/5">
        <CardContent className="pt-6">
          <p className="text-sm">
            <span className="font-medium">Rule of thumb:</span>{" "}
            <span className="text-muted-foreground">
              Fine-tuning is not prompt engineering. Prompt engineering tweaks the input;
              fine-tuning changes the model itself. Both are useful — fine-tuning pays off when
              you have a clear, consistent task and at least a few hundred examples.
            </span>
          </p>
        </CardContent>
      </Card>
    </div>
  )
}

function MethodsStep({
  level,
  onNavigate,
}: {
  level: ExperienceLevel
  onNavigate: (href: string) => void
}) {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-xl font-semibold">The 6 fine-tuning methods</h2>
        <p className="mt-1.5 text-sm text-muted-foreground">
          {level === "beginner"
            ? "Each method makes a different trade-off between VRAM cost, simplicity, and output quality."
            : "Quick reference — use the Methodology Selector for an interactive recommendation."}
        </p>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {METHODOLOGY_INFO.map((info) => (
          <MethodCard key={info.methodology} info={info} />
        ))}
      </div>

      {level === "beginner" ? (
        <Card className="border-emerald-500/30 bg-emerald-500/5">
          <CardContent className="pt-6">
            <p className="text-sm">
              <span className="font-medium text-foreground">Starting out?</span>{" "}
              <span className="text-muted-foreground">
                <strong>QLoRA</strong> is the recommended default. It runs on a single consumer
                GPU, needs as few as 500 samples, and produces results comparable to full SFT at
                a fraction of the compute cost.
              </span>
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="flex justify-end">
          <Button variant="outline" size="sm" onClick={() => onNavigate("/methodology")}>
            Open Methodology Selector
            <ChevronRight className="ml-1 size-3.5" />
          </Button>
        </div>
      )}
    </div>
  )
}

function ResourcesStep() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-xl font-semibold">What you&apos;ll need</h2>
        <p className="mt-1.5 text-sm text-muted-foreground">
          A checklist before you start your first training job.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader className="pb-3">
            <div className="flex size-8 items-center justify-center rounded-lg bg-blue-500/10">
              <Database className="size-4 text-blue-500" />
            </div>
            <CardTitle className="text-sm">A dataset</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-2 text-sm text-muted-foreground">
            <p>Minimum 500 examples for LoRA/QLoRA, 1,000+ for SFT.</p>
            <p>
              Formats supported: <strong className="text-foreground">Alpaca</strong>,{" "}
              <strong className="text-foreground">ShareGPT</strong>,{" "}
              <strong className="text-foreground">ChatML</strong>.
            </p>
            <p>The Dataset Studio will validate and format it for you.</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <div className="flex size-8 items-center justify-center rounded-lg bg-violet-500/10">
              <Cpu className="size-4 text-violet-500" />
            </div>
            <CardTitle className="text-sm">GPU access</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-2 text-sm text-muted-foreground">
            <p>QLoRA on a 7B model fits in ~10GB VRAM — a single RTX 3090 or cloud T4.</p>
            <p>The GPU Selector compares RunPod, Lambda Labs, AWS, GCP, and Azure pricing.</p>
            <p>No GPU? The Cost Estimator will show you what each option will cost first.</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <div className="flex size-8 items-center justify-center rounded-lg bg-emerald-500/10">
              <Layers className="size-4 text-emerald-500" />
            </div>
            <CardTitle className="text-sm">A base model</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-2 text-sm text-muted-foreground">
            <p>The Config Builder lets you pick from the model catalog.</p>
            <p>
              Good starting points: <strong className="text-foreground">Llama-3-8B</strong>,{" "}
              <strong className="text-foreground">Mistral-7B</strong>,{" "}
              <strong className="text-foreground">Phi-3-mini</strong>.
            </p>
            <p>Larger models need more VRAM but usually produce better results.</p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function TourStep({ level, onNavigate }: { level: ExperienceLevel; onNavigate: (href: string) => void }) {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-xl font-semibold">Studio overview</h2>
        <p className="mt-1.5 text-sm text-muted-foreground">
          {level === "beginner"
            ? "These are the modules you'll work through, in order."
            : "A map of the studio. Jump to any module from the sidebar."}
        </p>
      </div>

      <div className="flex flex-col gap-2">
        {STUDIO_MODULES.map((mod, i) => {
          const Icon = mod.icon
          return (
            <button
              key={mod.href}
              type="button"
              onClick={() => onNavigate(mod.href)}
              className="group flex items-center gap-4 rounded-lg border border-border bg-card px-4 py-3 text-left transition-colors hover:border-primary/50 hover:bg-primary/5"
            >
              <div className="flex size-8 shrink-0 items-center justify-center rounded-md bg-muted">
                <Icon className="size-4 text-muted-foreground group-hover:text-primary" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground">{mod.label}</p>
                <p className="text-xs text-muted-foreground">{mod.desc}</p>
              </div>
              {level === "beginner" && (
                <Badge variant="outline" className="shrink-0 text-xs">
                  Step {i + 1}
                </Badge>
              )}
              <ChevronRight className="size-4 shrink-0 text-muted-foreground/50 group-hover:text-primary" />
            </button>
          )
        })}
      </div>
    </div>
  )
}

function DoneStep({ level, onNavigate }: { level: ExperienceLevel; onNavigate: (href: string) => void }) {
  const destination = level === "beginner" ? "/datasets" : "/methodology"
  const destinationLabel = level === "beginner" ? "Dataset Studio" : "Methodology Selector"

  return (
    <div className="flex flex-col items-center gap-6 py-8 text-center">
      <div className="flex size-16 items-center justify-center rounded-full bg-primary/10">
        <CheckCircle2 className="size-8 text-primary" />
      </div>

      <div>
        <h2 className="text-xl font-semibold">You&apos;re ready to go</h2>
        <p className="mt-1.5 text-sm text-muted-foreground">
          {level === "beginner"
            ? "Start by uploading your dataset. The studio will guide you through the rest."
            : "Head to the Methodology Selector to configure your first training run."}
        </p>
      </div>

      <div className="flex flex-col items-center gap-3 sm:flex-row">
        <Button size="lg" onClick={() => onNavigate(destination)}>
          Go to {destinationLabel}
          <ArrowRight className="ml-2 size-4" />
        </Button>
        <Button variant="outline" size="lg" onClick={() => onNavigate("/dashboard")}>
          Dashboard
        </Button>
      </div>
    </div>
  )
}

// ── Main wizard ────────────────────────────────────────────────────────────

export default function OnboardingPage() {
  const router = useRouter()
  const [level, setLevel] = useState<ExperienceLevel | null>(null)
  const [stepIndex, setStepIndex] = useState(0)

  const steps: WizardStep[] = level === "advanced" ? [...ADVANCED_STEPS] : [...BEGINNER_STEPS]
  const currentStep = steps[stepIndex] as WizardStep

  function handleSelectLevel(selected: ExperienceLevel) {
    setLevel(selected)
    setStepIndex(1)
  }

  function handleNavigate(href: string) {
    router.push(href)
  }

  function back() {
    setStepIndex((i) => Math.max(0, i - 1))
  }

  function next() {
    setStepIndex((i) => Math.min(steps.length - 1, i + 1))
  }

  const isFirst = stepIndex === 0
  const isLast = stepIndex === steps.length - 1
  const showNav = currentStep !== "experience" && currentStep !== "done"

  return (
    <PageContainer className="max-w-4xl">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-foreground">Onboarding</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Get oriented before your first fine-tuning run.
        </p>
      </div>

      {level !== null && !isFirst && (
        <StepProgress current={stepIndex} total={steps.length} />
      )}

      <div className="min-h-[420px]">
        {currentStep === "experience" && <ExperienceStep onSelect={handleSelectLevel} />}
        {currentStep === "what-is-ft" && <WhatIsFineTuningStep />}
        {currentStep === "methods" && (
          <MethodsStep level={level ?? "beginner"} onNavigate={handleNavigate} />
        )}
        {currentStep === "resources" && <ResourcesStep />}
        {currentStep === "tour" && (
          <TourStep level={level ?? "beginner"} onNavigate={handleNavigate} />
        )}
        {currentStep === "done" && (
          <DoneStep level={level ?? "beginner"} onNavigate={handleNavigate} />
        )}
      </div>

      {showNav && (
        <div className="mt-8 flex items-center justify-between border-t border-border pt-6">
          <Button variant="outline" onClick={back} disabled={isFirst}>
            <ArrowLeft className="mr-2 size-4" />
            Back
          </Button>
          <Button onClick={next} disabled={isLast}>
            {stepIndex === steps.length - 2 ? "Finish" : "Next"}
            <ArrowRight className="ml-2 size-4" />
          </Button>
        </div>
      )}
    </PageContainer>
  )
}
