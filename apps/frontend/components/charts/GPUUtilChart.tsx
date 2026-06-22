"use client"

import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"

import type { TrainingMetricsUpdate } from "@/types"

export function GPUUtilChart({ data }: { data: TrainingMetricsUpdate[] }) {
  if (data.length === 0) {
    return <p className="text-sm text-muted-foreground">No GPU metrics yet.</p>
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="step" fontSize={12} />
        <YAxis domain={[0, 100]} unit="%" fontSize={12} />
        <Tooltip />
        <Line
          type="monotone"
          dataKey="gpu_utilization_pct"
          name="GPU utilization"
          stroke="#16a34a"
          dot={false}
          connectNulls
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
