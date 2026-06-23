"use client"

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"

export type MetricComparisonPoint = {
  run_id: string
  value: number
  label: string
}

export function MetricComparisonChart({ data }: { data: MetricComparisonPoint[] }) {
  if (data.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">No runs with this metric recorded yet.</p>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="label" fontSize={12} />
        <YAxis fontSize={12} />
        <Tooltip />
        <Bar dataKey="value" fill="#2563eb" />
      </BarChart>
    </ResponsiveContainer>
  )
}
