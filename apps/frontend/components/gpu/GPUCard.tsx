"use client"

import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import type { GpuPricingResponse } from "@/types"

export function GPUCard({
  instance,
  selected,
  onSelect,
}: {
  instance: GpuPricingResponse
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
          <CardTitle>{instance.gpu_type}</CardTitle>
          {selected ? <Badge>Selected</Badge> : null}
        </div>
        <CardDescription>{instance.vendor}</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-1 text-sm text-muted-foreground">
        <p>VRAM: {instance.vram_gb} GB</p>
        <p>Price: ${instance.price_per_hour_usd.toFixed(2)} / hr</p>
      </CardContent>
    </Card>
  )
}
