"use client"

import { useMemo, useState } from "react"
import { useRouter } from "next/navigation"

import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { MethodologyCard, METHODOLOGY_INFO } from "@/components/training/MethodologyCard"
import {
  recommendMethodology,
  type RecommendationGoal,
  type VramBudget,
} from "@/lib/methodology-recommendation"
import type { Methodology } from "@/types"

const GOAL_OPTIONS: { value: RecommendationGoal; label: string }[] = [
  { value: "plain_task", label: "Plain task (instruction following, style, domain knowledge)" },
  { value: "alignment", label: "Preference alignment (chosen vs. rejected responses)" },
]

const VRAM_OPTIONS: { value: VramBudget; label: string }[] = [
  { value: "low", label: "Low — single consumer GPU (≤16GB)" },
  { value: "medium", label: "Medium — one datacenter GPU (24–48GB)" },
  { value: "high", label: "High — multi-GPU or 80GB+ class" },
]

export function MethodologyRecommender() {
  const router = useRouter()
  const [goal, setGoal] = useState<RecommendationGoal>("plain_task")
  const [vramBudget, setVramBudget] = useState<VramBudget>("medium")
  const [datasetRowsInput, setDatasetRowsInput] = useState("")
  const [selected, setSelected] = useState<Methodology>(
    () => recommendMethodology({ goal: "plain_task", vramBudget: "medium", datasetRows: 0 }).methodology
  )

  const datasetRows = Number(datasetRowsInput) || 0

  const recommendation = useMemo(
    () => recommendMethodology({ goal, vramBudget, datasetRows }),
    [goal, vramBudget, datasetRows]
  )

  const selectedInfo = METHODOLOGY_INFO.find((info) => info.methodology === selected)

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader>
          <CardTitle>Get a recommendation</CardTitle>
          <CardDescription>
            Answer a few questions to highlight a starting-point methodology below. This is a
            rule of thumb, not a guarantee — compare the full table before committing.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="reco-goal">Goal</Label>
            <Select value={goal} onValueChange={(value) => setGoal(value as RecommendationGoal)}>
              <SelectTrigger id="reco-goal" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {GOAL_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="reco-vram">VRAM budget</Label>
            <Select
              value={vramBudget}
              onValueChange={(value) => setVramBudget(value as VramBudget)}
            >
              <SelectTrigger id="reco-vram" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {VRAM_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="reco-rows">
              Approx. dataset size {goal === "alignment" ? "(pairs)" : "(rows)"}
            </Label>
            <Input
              id="reco-rows"
              type="number"
              min={0}
              placeholder="e.g. 2000"
              value={datasetRowsInput}
              onChange={(event) => setDatasetRowsInput(event.target.value)}
            />
          </div>
        </CardContent>
      </Card>

      <Alert>
        <AlertDescription className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <span>
            Recommended methodology:{" "}
            <strong className="text-foreground">
              {METHODOLOGY_INFO.find((info) => info.methodology === recommendation.methodology)
                ?.label}
            </strong>
          </span>
          <Button
            type="button"
            size="sm"
            variant="outline"
            onClick={() => setSelected(recommendation.methodology)}
            disabled={selected === recommendation.methodology}
          >
            Use recommended
          </Button>
        </AlertDescription>
      </Alert>

      {recommendation.belowMinSamples ? (
        <Alert variant="destructive">
          <AlertDescription>
            {datasetRows.toLocaleString()} is below the recommended minimum sample count for{" "}
            {METHODOLOGY_INFO.find((info) => info.methodology === recommendation.methodology)?.label}
            . Consider a smaller-footprint methodology or growing the dataset first.
          </AlertDescription>
        </Alert>
      ) : null}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {METHODOLOGY_INFO.map((info) => (
          <MethodologyCard
            key={info.methodology}
            info={info}
            selected={selected === info.methodology}
            recommended={recommendation.methodology === info.methodology}
            onSelect={() => setSelected(info.methodology)}
          />
        ))}
      </div>

      <div className="flex items-center justify-end gap-3">
        <p className="text-sm text-muted-foreground">
          Selected: <span className="text-foreground">{selectedInfo?.label}</span>
        </p>
        <Button type="button" onClick={() => router.push(`/config?methodology=${selected}`)}>
          Continue to training config
        </Button>
      </div>
    </div>
  )
}
