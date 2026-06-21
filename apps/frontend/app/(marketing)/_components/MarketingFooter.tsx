import Link from "next/link"

const FOOTER_LINKS = [
  { href: "https://github.com/anulsasidharan/llm-finetuning-studio", label: "GitHub" },
  { href: "https://huggingface.co/docs/peft", label: "PEFT docs" },
  { href: "https://huggingface.co/docs/trl", label: "TRL docs" },
] as const

function MarketingFooter() {
  return (
    <footer className="border-t border-border">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-4 px-4 py-10 sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
        <p className="text-sm text-muted-foreground">
          &copy; {new Date().getFullYear()} LLM Fine-Tuning Studio &middot; built by{" "}
          <Link
            href="https://github.com/anulsasidharan"
            className="font-medium text-foreground hover:text-primary"
          >
            OrionVexa
          </Link>
        </p>
        <nav className="flex items-center gap-6">
          {FOOTER_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              {link.label}
            </Link>
          ))}
        </nav>
      </div>
    </footer>
  )
}

export { MarketingFooter }
