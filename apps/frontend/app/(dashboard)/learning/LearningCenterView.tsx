"use client"

import Link from "next/link"
import { useRouter, useSearchParams } from "next/navigation"
import { useCallback, useMemo } from "react"
import {
  ArrowRight,
  BookOpen,
  Brain,
  Database,
  GitBranch,
  Lightbulb,
  type LucideIcon,
} from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { PageContainer } from "@/components/layout/PageContainer"
import {
  DEFAULT_LEARNING_TOPIC_ID,
  getTopicById,
  LEARNING_CATEGORIES,
  LEARNING_TOPICS,
  type LearningCategory,
  type LearningSection,
  type LearningTopic,
} from "@/lib/learning-center-data"
import type { Methodology } from "@/types"
import { cn } from "@/lib/utils"

const CATEGORY_ICONS: Record<LearningCategory, LucideIcon> = {
  foundations: BookOpen,
  datasets: Database,
  methodologies: GitBranch,
  concepts: Brain,
}

const METHODOLOGY_COLORS: Record<Methodology, string> = {
  sft: "bg-blue-500/10 border-blue-500/30 text-blue-700 dark:text-blue-400",
  lora: "bg-violet-500/10 border-violet-500/30 text-violet-700 dark:text-violet-400",
  qlora: "bg-emerald-500/10 border-emerald-500/30 text-emerald-700 dark:text-emerald-400",
  dpo: "bg-orange-500/10 border-orange-500/30 text-orange-700 dark:text-orange-400",
  orpo: "bg-pink-500/10 border-pink-500/30 text-pink-700 dark:text-pink-400",
  rlhf: "bg-amber-500/10 border-amber-500/30 text-amber-700 dark:text-amber-400",
}

const CALLOUT_STYLES = {
  tip: "border-emerald-500/30 bg-emerald-500/5",
  info: "border-blue-500/30 bg-blue-500/5",
  warning: "border-amber-500/30 bg-amber-500/5",
} as const

function SectionBlock({ section }: { section: LearningSection }) {
  return (
    <div className="flex flex-col gap-2">
      {section.heading ? (
        <h3 className="text-sm font-semibold text-foreground">{section.heading}</h3>
      ) : null}
      {section.body ? (
        <p className="text-sm leading-relaxed text-muted-foreground">{section.body}</p>
      ) : null}
      {section.bullets ? (
        <ul className="list-disc space-y-1.5 pl-5 text-sm text-muted-foreground">
          {section.bullets.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : null}
      {section.callout ? (
        <Card className={cn("border", CALLOUT_STYLES[section.callout.variant])}>
          <CardContent className="pt-4">
            {section.callout.title ? (
              <p className="text-sm font-medium text-foreground">{section.callout.title}</p>
            ) : null}
            <p className="text-sm text-muted-foreground">{section.callout.text}</p>
          </CardContent>
        </Card>
      ) : null}
    </div>
  )
}

function TopicArticle({ topic }: { topic: LearningTopic }) {
  const categoryLabel = LEARNING_CATEGORIES.find((c) => c.id === topic.category)?.label

  return (
    <article className="flex flex-col gap-6">
      <div>
        <div className="flex flex-wrap items-center gap-2">
          {categoryLabel ? (
            <Badge variant="outline" className="text-xs">
              {categoryLabel}
            </Badge>
          ) : null}
          {topic.methodology ? (
            <Badge
              variant="outline"
              className={cn("text-xs uppercase", METHODOLOGY_COLORS[topic.methodology])}
            >
              {topic.methodology}
            </Badge>
          ) : null}
        </div>
        <h2 className="mt-3 text-xl font-semibold text-foreground">{topic.title}</h2>
        <p className="mt-1.5 text-sm text-muted-foreground">{topic.summary}</p>
      </div>

      <div className="flex flex-col gap-5">
        {topic.sections.map((section, index) => (
          <div key={`${topic.id}-section-${index}`}>
            <SectionBlock section={section} />
            {index < topic.sections.length - 1 ? <Separator className="mt-5" /> : null}
          </div>
        ))}
      </div>

      {topic.relatedLinks && topic.relatedLinks.length > 0 ? (
        <div className="flex flex-col gap-3 rounded-xl border border-border bg-muted/30 p-4">
          <div className="flex items-center gap-2 text-sm font-medium text-foreground">
            <Lightbulb className="size-4 text-primary" />
            Try it in the studio
          </div>
          <div className="flex flex-wrap gap-2">
            {topic.relatedLinks.map((link) => (
              <Button key={link.href} variant="outline" size="sm" render={<Link href={link.href} />}>
                {link.label}
                <ArrowRight className="size-3.5" />
              </Button>
            ))}
          </div>
        </div>
      ) : null}
    </article>
  )
}

function LearningCenterView() {
  const router = useRouter()
  const searchParams = useSearchParams()

  const activeTopicId = useMemo(() => {
    const requested = searchParams.get("topic")
    if (requested && getTopicById(requested)) {
      return requested
    }
    return DEFAULT_LEARNING_TOPIC_ID
  }, [searchParams])

  const activeTopic = getTopicById(activeTopicId) ?? getTopicById(DEFAULT_LEARNING_TOPIC_ID)!

  const selectTopic = useCallback(
    (topicId: string) => {
      const params = new URLSearchParams(searchParams.toString())
      params.set("topic", topicId)
      router.replace(`/learning?${params.toString()}`, { scroll: false })
    },
    [router, searchParams]
  )

  return (
    <PageContainer className="flex flex-col gap-6">
      <div>
        <h1 className="font-heading text-2xl font-semibold text-foreground">Learning Center</h1>
        <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
          Conceptual explainers for fine-tuning — browse anytime while you configure datasets,
          pick a methodology, or tune hyperparameters.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,15rem)_1fr] lg:gap-8">
        <nav aria-label="Learning topics" className="flex flex-col gap-5">
          {LEARNING_CATEGORIES.map((category) => {
            const Icon = CATEGORY_ICONS[category.id]
            const topics = LEARNING_TOPICS.filter((topic) => topic.category === category.id)

            return (
              <div key={category.id} className="flex flex-col gap-2">
                <div className="flex items-center gap-2 px-1">
                  <Icon className="size-4 text-muted-foreground" />
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-foreground">
                      {category.label}
                    </p>
                    <p className="text-xs text-muted-foreground">{category.description}</p>
                  </div>
                </div>
                <ul className="flex flex-col gap-0.5">
                  {topics.map((topic) => {
                    const active = topic.id === activeTopicId
                    return (
                      <li key={topic.id}>
                        <button
                          type="button"
                          onClick={() => selectTopic(topic.id)}
                          aria-current={active ? "page" : undefined}
                          className={cn(
                            "w-full rounded-lg px-3 py-2 text-left text-sm transition-colors",
                            active
                              ? "bg-secondary font-medium text-secondary-foreground"
                              : "text-muted-foreground hover:bg-muted hover:text-foreground"
                          )}
                        >
                          {topic.title}
                        </button>
                      </li>
                    )
                  })}
                </ul>
              </div>
            )
          })}
        </nav>

        <Card className="min-w-0">
          <CardContent className="pt-6">
            <TopicArticle topic={activeTopic} />
          </CardContent>
        </Card>
      </div>
    </PageContainer>
  )
}

export { LearningCenterView }
