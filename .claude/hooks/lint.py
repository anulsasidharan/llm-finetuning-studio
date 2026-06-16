#!/usr/bin/env python3
"""
PostToolUse hook — auto-fix lint/format errors after every Write/Edit.
Reads the tool call JSON from stdin and runs the right linter for the file type.
"""
import json
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], cwd: str | None = None) -> None:
    subprocess.run(cmd, cwd=cwd, capture_output=True)


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    file_path = data.get("tool_input", {}).get("file_path", "")
    if not file_path:
        sys.exit(0)

    p = Path(file_path)
    if not p.exists() or not p.is_file():
        sys.exit(0)

    if p.suffix == ".py":
        run(["ruff", "check", "--fix", str(p)])
        run(["ruff", "format", str(p)])

    elif p.suffix in {".ts", ".tsx", ".js", ".jsx"}:
        # Walk up from the file to find the nearest package.json root
        parent = p.parent
        while parent != parent.parent:
            if (parent / "package.json").exists():
                run(["npx", "eslint", "--fix", str(p)], cwd=str(parent))
                break
            parent = parent.parent


if __name__ == "__main__":
    main()
