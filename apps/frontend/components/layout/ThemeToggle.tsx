"use client"

import { Moon, Sun } from "lucide-react"
import { useTheme } from "next-themes"
import { useSyncExternalStore } from "react"

import { Button } from "@/components/ui/button"

function subscribeNoop() {
  return () => {}
}

function useIsClient() {
  return useSyncExternalStore(subscribeNoop, () => true, () => false)
}

function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme()
  const mounted = useIsClient()

  return (
    <Button
      variant="ghost"
      size="icon"
      aria-label="Toggle theme"
      onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
    >
      {mounted && resolvedTheme === "dark" ? (
        <Sun className="size-4" />
      ) : (
        <Moon className="size-4" />
      )}
    </Button>
  )
}

export { ThemeToggle }
