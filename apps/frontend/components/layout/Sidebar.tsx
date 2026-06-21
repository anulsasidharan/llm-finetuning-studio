"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  Activity,
  Beaker,
  Box,
  Calculator,
  Cpu,
  Database,
  GitBranch,
  LayoutDashboard,
  Rocket,
  SlidersHorizontal,
  UploadCloud,
  FlaskConical,
  type LucideIcon,
} from "lucide-react"

import { cn } from "@/lib/utils"
import { ScrollArea } from "@/components/ui/scroll-area"

type NavItem = {
  label: string
  href: string
  icon: LucideIcon
}

const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Onboarding", href: "/onboarding", icon: Rocket },
  { label: "Datasets", href: "/datasets", icon: Database },
  { label: "Methodology", href: "/methodology", icon: GitBranch },
  { label: "Training Config", href: "/config", icon: SlidersHorizontal },
  { label: "GPU Selector", href: "/gpu-selector", icon: Cpu },
  { label: "Cost Estimator", href: "/cost-estimator", icon: Calculator },
  { label: "Training", href: "/training", icon: Activity },
  { label: "Evaluation", href: "/evaluation", icon: FlaskConical },
  { label: "Experiments", href: "/experiments", icon: Beaker },
  { label: "Models", href: "/models", icon: Box },
  { label: "Deploy", href: "/deploy", icon: UploadCloud },
]

function isActiveRoute(pathname: string, href: string) {
  return pathname === href || pathname.startsWith(`${href}/`)
}

function Sidebar() {
  const pathname = usePathname()

  return (
    <aside
      data-slot="sidebar"
      className="hidden h-svh w-60 shrink-0 flex-col border-r border-border bg-card sm:flex"
    >
      <div className="flex h-14 shrink-0 items-center gap-2 border-b border-border px-4">
        <Link href="/dashboard" className="flex items-center gap-2 font-heading text-sm font-semibold text-foreground">
          <span className="flex size-7 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <FlaskConical className="size-3.5" />
          </span>
          Fine-Tuning Studio
        </Link>
      </div>
      <ScrollArea className="flex-1">
        <nav className="flex flex-col gap-1 p-3">
          {NAV_ITEMS.map(({ label, href, icon: Icon }) => {
            const active = isActiveRoute(pathname, href)
            return (
              <Link
                key={href}
                href={href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground",
                  active && "bg-secondary text-secondary-foreground"
                )}
              >
                <Icon className="size-4 shrink-0" />
                {label}
              </Link>
            )
          })}
        </nav>
      </ScrollArea>
    </aside>
  )
}

export { Sidebar, NAV_ITEMS }
