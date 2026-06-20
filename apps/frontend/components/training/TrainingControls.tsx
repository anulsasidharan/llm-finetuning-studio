"use client"

import { Button } from "@/components/ui/button"
import type { FineTuneJobStatus } from "@/types"

// Skeleton only — Phase 2 wires these to real start/pause/cancel job actions.
export function TrainingControls({ status }: { status: FineTuneJobStatus }) {
  const canStart = status === "pending"
  const canPause = status === "running"
  const canCancel = status === "pending" || status === "queued" || status === "running"

  return (
    <div className="flex gap-2">
      <Button type="button" disabled={!canStart} title="Coming in Phase 2">
        Start
      </Button>
      <Button type="button" variant="outline" disabled={!canPause} title="Coming in Phase 2">
        Pause
      </Button>
      <Button
        type="button"
        variant="destructive"
        disabled={!canCancel}
        title="Coming in Phase 2"
      >
        Cancel
      </Button>
    </div>
  )
}
