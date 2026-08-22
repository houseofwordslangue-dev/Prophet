#!/usr/bin/env python3
"""GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md

Fail when a newly added process file does not explicitly acknowledge the
controlling project instruction.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

MASTER = "MASTER-OVERRIDING-SITE-INSTRUCTION.md"
DECLARATION = f"GOVERNED_BY: {MASTER}"
PROCESS_PREFIXES = (".github/workflows/", "scripts/")
PROCESS_SUFFIXES = (".yml", ".yaml", ".py", ".js", ".mjs", ".cjs", ".sh", ".ts")
SELF = Path(__file__).as_posix()


def sh(*args: str) -> str:
    return subprocess.check_output(args, text=True).strip()


def base_ref() -> str | None:
    event = os.environ.get("GITHUB_EVENT_NAME", "")
    if event == "pull_request":
        ref = os.environ.get("GITHUB_BASE_REF")
        return f"origin/{ref}" if ref else None
    before = os.environ.get("GITHUB_EVENT_BEFORE") or os.environ.get("GITHUB_BEFORE")
    if before and set(before) != {"0"}:
        return before
    try:
        return sh("git", "rev-parse", "HEAD^")
    except Exception:
        return None


def newly_added_files(base: str | None) -> list[str]:
    if not base:
        return []
    try:
        out = sh("git", "diff", "--diff-filter=A", "--name-only", f"{base}...HEAD")
    except Exception:
        out = sh("git", "diff", "--diff-filter=A", "--name-only", base, "HEAD")
    return [x for x in out.splitlines() if x.strip()]


def is_process(path: str) -> bool:
    if path == SELF:
        return False
    return path.startswith(PROCESS_PREFIXES) and path.endswith(PROCESS_SUFFIXES)


def main() -> int:
    master = Path(MASTER)
    if not master.is_file():
        print(f"ERROR: controlling master instruction missing: {MASTER}", file=sys.stderr)
        return 2

    base = base_ref()
    candidates = [p for p in newly_added_files(base) if is_process(p)]
    violations: list[str] = []
    for path in candidates:
        try:
            text = Path(path).read_text(encoding="utf-8")
        except Exception as exc:
            violations.append(f"{path}: unreadable ({exc})")
            continue
        if DECLARATION not in text:
            violations.append(path)

    if violations:
        print("New project processes must explicitly acknowledge the controlling master instruction.", file=sys.stderr)
        print(f"Required declaration: {DECLARATION}", file=sys.stderr)
        for path in violations:
            print(f" - {path}", file=sys.stderr)
        return 1

    print(f"Master-governance check PASS. New process files checked: {len(candidates)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
