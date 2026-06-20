import { Badge } from "@/components/ui/badge"
import type { FineTuneJobStatus } from "@/types"

const STATUS_LABEL: Record<FineTuneJobStatus, string> = {
  pending: "Pending",
  queued: "Queued",
  running: "Running",
  completed: "Completed",
  failed: "Failed",
  cancelled: "Cancelled",
}

const STATUS_VARIANT: Record<
  FineTuneJobStatus,
  "default" | "secondary" | "destructive" | "outline"
> = {
  pending: "outline",
  queued: "secondary",
  running: "default",
  completed: "default",
  failed: "destructive",
  cancelled: "outline",
}

export function JobStatusBadge({ status }: { status: FineTuneJobStatus }) {
  return <Badge variant={STATUS_VARIANT[status]}>{STATUS_LABEL[status]}</Badge>
}
