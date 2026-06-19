import { AccountMenu } from "@/components/layout/AccountMenu"

function Header() {
  return (
    <header
      data-slot="header"
      className="flex h-14 shrink-0 items-center justify-between border-b border-border bg-background px-4 sm:px-6"
    >
      <span className="text-sm font-medium text-muted-foreground">
        LLM Fine-Tuning Studio
      </span>
      <AccountMenu />
    </header>
  )
}

export { Header }
