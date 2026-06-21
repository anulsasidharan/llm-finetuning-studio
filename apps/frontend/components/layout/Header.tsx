"use client"

import { usePathname } from "next/navigation"

import { AccountMenu } from "@/components/layout/AccountMenu"
import { NAV_ITEMS } from "@/components/layout/Sidebar"
import { ThemeToggle } from "@/components/layout/ThemeToggle"

function getPageTitle(pathname: string): string {
  const match = NAV_ITEMS.find(
    (item) => pathname === item.href || pathname.startsWith(`${item.href}/`)
  )
  return match?.label ?? "Dashboard"
}

function Header() {
  const pathname = usePathname()

  return (
    <header
      data-slot="header"
      className="flex h-14 shrink-0 items-center justify-between border-b border-border bg-background px-4 sm:px-6"
    >
      <span className="font-heading text-sm font-semibold text-foreground">
        {getPageTitle(pathname)}
      </span>
      <div className="flex items-center gap-1">
        <ThemeToggle />
        <AccountMenu />
      </div>
    </header>
  )
}

export { Header }
