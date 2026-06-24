"use client"

import { Button } from "@/components/ui/button"

export function VendorFilter({
  vendors,
  selectedVendor,
  onSelectVendor,
}: {
  vendors: string[]
  selectedVendor: string | null
  onSelectVendor: (vendor: string | null) => void
}) {
  return (
    <div className="flex flex-wrap gap-2" role="group" aria-label="Filter by cloud vendor">
      <Button
        type="button"
        size="sm"
        variant={selectedVendor === null ? "default" : "outline"}
        onClick={() => onSelectVendor(null)}
      >
        All vendors
      </Button>
      {vendors.map((vendor) => (
        <Button
          key={vendor}
          type="button"
          size="sm"
          variant={selectedVendor === vendor ? "default" : "outline"}
          onClick={() => onSelectVendor(vendor)}
        >
          {vendor}
        </Button>
      ))}
    </div>
  )
}
