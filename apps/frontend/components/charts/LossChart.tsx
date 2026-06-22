"use client"

import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"

import type { TrainingMetricsUpdate } from "@/types"

export function LossChart({ data }: { data: TrainingMetricsUpdate[] }) {
  if (data.length === 0) {
    return <p className="text-sm text-muted-foreground">No metrics yet — waiting for training to start.</p>
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="step" fontSize={12} />
        <YAxis fontSize={12} />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="train_loss" name="Train loss" stroke="#2563eb" dot={false} connectNulls />
        <Line type="monotone" dataKey="eval_loss" name="Eval loss" stroke="#dc2626" dot={false} connectNulls />
      </LineChart>
    </ResponsiveContainer>
  )
}
