import type { ReactNode } from "react"

import { Label } from "@/components/ui/label"
import { ParameterTooltip } from "@/components/training/ParameterTooltip"
import type { ParameterInfo } from "@/components/training/ParameterTooltip"

export function ParameterField({
  id,
  label,
  error,
  info,
  children,
}: {
  id: string
  label: string
  error?: string
  info?: ParameterInfo
  children: ReactNode
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center gap-1">
        <Label htmlFor={id}>{label}</Label>
        {info ? <ParameterTooltip {...info} /> : null}
      </div>
      {children}
      {error ? <p className="text-sm text-destructive">{error}</p> : null}
    </div>
  )
}
