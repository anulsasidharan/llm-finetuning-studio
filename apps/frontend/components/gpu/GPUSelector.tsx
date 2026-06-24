"use client"

import { useMemo, useState } from "react"
import { useRouter } from "next/navigation"

import { Button } from "@/components/ui/button"
import { CostCard } from "@/components/gpu/CostCard"
import { GPUCard } from "@/components/gpu/GPUCard"
import { VendorFilter } from "@/components/gpu/VendorFilter"
import { useGPUPricing } from "@/hooks/useGPUPricing"
import type { GpuPricingResponse } from "@/types"

function instanceKey(instance: GpuPricingResponse): string {
  return `${instance.vendor}:${instance.gpu_type}`
}

export function GPUSelector() {
  const router = useRouter()
  const gpuPricingQuery = useGPUPricing()
  const [selectedVendor, setSelectedVendor] = useState<string | null>(null)
  const [selectedKey, setSelectedKey] = useState<string | null>(null)

  const instances = useMemo(() => gpuPricingQuery.data ?? [], [gpuPricingQuery.data])

  const vendors = useMemo(
    () => Array.from(new Set(instances.map((instance) => instance.vendor))).sort(),
    [instances]
  )

  const filteredInstances = useMemo(
    () =>
      selectedVendor === null
        ? instances
        : instances.filter((instance) => instance.vendor === selectedVendor),
    [instances, selectedVendor]
  )

  const selectedInstance = instances.find((instance) => instanceKey(instance) === selectedKey)

  return (
    <div className="flex flex-col gap-6">
      {gpuPricingQuery.isLoading ? (
        <p className="text-sm text-muted-foreground">Loading GPU pricing...</p>
      ) : null}

      {gpuPricingQuery.isSuccess && instances.length === 0 ? (
        <p className="text-sm text-muted-foreground">No GPU instances available yet.</p>
      ) : null}

      {vendors.length > 0 ? (
        <VendorFilter vendors={vendors} selectedVendor={selectedVendor} onSelectVendor={setSelectedVendor} />
      ) : null}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {filteredInstances.map((instance) => (
          <GPUCard
            key={instanceKey(instance)}
            instance={instance}
            selected={selectedKey === instanceKey(instance)}
            onSelect={() => setSelectedKey(instanceKey(instance))}
          />
        ))}
      </div>

      {selectedInstance ? <CostCard instance={selectedInstance} /> : null}

      <div className="flex items-center justify-end gap-3">
        <p className="text-sm text-muted-foreground">
          Selected:{" "}
          <span className="text-foreground">
            {selectedInstance ? `${selectedInstance.vendor} ${selectedInstance.gpu_type}` : "None"}
          </span>
        </p>
        <Button
          type="button"
          disabled={!selectedInstance}
          onClick={() => {
            if (!selectedInstance) return
            router.push(
              `/config?gpu_type=${encodeURIComponent(selectedInstance.gpu_type)}&cloud_vendor=${encodeURIComponent(selectedInstance.vendor)}`
            )
          }}
        >
          Continue to training config
        </Button>
      </div>
    </div>
  )
}
