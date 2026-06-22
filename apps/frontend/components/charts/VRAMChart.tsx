"use client"

import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"

import type { TrainingMetricsUpdate } from "@/types"

export function VRAMChart({ data }: { data: TrainingMetricsUpdate[] }) {
  if (data.length === 0) {
    return <p className="text-sm text-muted-foreground">No VRAM metrics yet.</p>
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="step" fontSize={12} />
        <YAxis unit=" GB" fontSize={12} />
        <Tooltip />
        <Line
          type="monotone"
          dataKey="vram_used_gb"
          name="VRAM used"
          stroke="#9333ea"
          dot={false}
          connectNulls
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
