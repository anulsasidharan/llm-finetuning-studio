"use client"

import { cn } from "@/lib/utils"
import { METHODOLOGY_INFO, type MethodologyInfo } from "@/lib/methodology-data"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export { METHODOLOGY_INFO, type MethodologyInfo }

export function MethodologyCard({
  info,
  selected,
  onSelect,
}: {
  info: MethodologyInfo
  selected: boolean
  onSelect: () => void
}) {
  return (
    <Card
      role="button"
      tabIndex={0}
      aria-pressed={selected}
      onClick={onSelect}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault()
          onSelect()
        }
      }}
      className={cn(
        "cursor-pointer transition-colors",
        selected ? "border-primary ring-1 ring-primary" : "hover:border-foreground/30"
      )}
    >
      <CardHeader>
        <div className="flex items-center justify-between gap-2">
          <CardTitle>{info.label}</CardTitle>
          {selected ? <Badge>Selected</Badge> : null}
        </div>
        <CardDescription>{info.keyDifferentiator}</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-1 text-sm text-muted-foreground">
        <p>Trainer: {info.trainerClass}</p>
        <p>VRAM usage: {info.vramUsage}</p>
        <p>Min samples: {info.minSamples}</p>
      </CardContent>
    </Card>
  )
}
