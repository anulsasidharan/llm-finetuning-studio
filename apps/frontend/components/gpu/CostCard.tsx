import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import type { GpuPricingResponse } from "@/types"

const PROJECTION_HOURS: { label: string; hours: number }[] = [
  { label: "1 hour", hours: 1 },
  { label: "8 hours", hours: 8 },
  { label: "24 hours", hours: 24 },
  { label: "1 week", hours: 24 * 7 },
]

export function CostCard({ instance }: { instance: GpuPricingResponse }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Estimated cost</CardTitle>
        <CardDescription>
          {instance.vendor} {instance.gpu_type} at ${instance.price_per_hour_usd.toFixed(2)}/hr
        </CardDescription>
      </CardHeader>
      <CardContent className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {PROJECTION_HOURS.map((projection) => (
          <div key={projection.label} className="flex flex-col gap-1">
            <p className="text-sm text-muted-foreground">{projection.label}</p>
            <p className="text-lg font-semibold">
              ${(instance.price_per_hour_usd * projection.hours).toFixed(2)}
            </p>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
