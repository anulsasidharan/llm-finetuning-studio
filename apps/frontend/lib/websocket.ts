"use client"

import { useEffect, useRef, useState } from "react"

import { getAccessToken } from "@/lib/api"
import type { FineTuneJobStatus, TrainingMetricsUpdate, TrainingSocketMessage } from "@/types"

// Cap in-memory history so a long-running job's chart data doesn't grow unbounded.
const MAX_METRICS_HISTORY = 500

export type TrainingSocketConnectionState = "idle" | "connecting" | "open" | "closed" | "error"

export type TrainingSocketState = {
  connectionState: TrainingSocketConnectionState
  status: FineTuneJobStatus | null
  metrics: TrainingMetricsUpdate[]
}

// Connects to WS /ws/training/{job_id} (apps/backend/websocket/training_hub.py) and exposes
// live metrics_update/status_change events. Auth is JWT-as-query-param — the only option,
// since browsers can't attach an Authorization header to a WebSocket handshake. Never
// auto-reconnects: a closed/errored socket stays closed until `enabled` flips (e.g. the
// caller re-mounts on a fresh jobId) — the backend itself only ever pushes, so silently
// retrying forever against a finished or unauthorized job would be pointless.
export function useTrainingSocket(jobId: string | undefined, enabled: boolean): TrainingSocketState {
  const [connectionState, setConnectionState] = useState<TrainingSocketConnectionState>("idle")
  const [status, setStatus] = useState<FineTuneJobStatus | null>(null)
  const [metrics, setMetrics] = useState<TrainingMetricsUpdate[]>([])
  const socketRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    if (!enabled || !jobId) return

    const token = getAccessToken()
    if (!token) {
      // Deferred via queueMicrotask, not called inline — setState directly in an
      // effect's synchronous body triggers cascading renders (react-hooks/set-state-in-effect).
      queueMicrotask(() => setConnectionState("error"))
      return
    }

    const socket = new WebSocket(
      `${process.env.NEXT_PUBLIC_WS_URL}/ws/training/${jobId}?token=${token}`
    )
    socketRef.current = socket
    queueMicrotask(() => setConnectionState("connecting"))

    socket.onopen = () => setConnectionState("open")
    socket.onerror = () => setConnectionState("error")
    socket.onclose = () => setConnectionState((prev) => (prev === "error" ? prev : "closed"))
    socket.onmessage = (event: MessageEvent<string>) => {
      let data: TrainingSocketMessage
      try {
        data = JSON.parse(event.data)
      } catch {
        return
      }
      if (data.type === "metrics_update") {
        setMetrics((prev) => [...prev.slice(-(MAX_METRICS_HISTORY - 1)), data])
      } else if (data.type === "status_change") {
        setStatus(data.status)
      }
    }

    return () => {
      socket.close()
      socketRef.current = null
    }
  }, [jobId, enabled])

  return { connectionState, status, metrics }
}
