#!/usr/bin/env python3
"""GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md

Deterministic acceptance audit for current Prophet-site standing instructions.
This audit validates repository invariants only; it never fabricates historical
content and never treats a numerical target as a substitute for source evidence.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "MASTER-OVERRIDING-SITE-INSTRUCTION.md"
BASE = ROOT / "MASTER-OVERRIDING-SITE-INSTRUCTION-BASE.md"
README = ROOT / "README.md"
CHILD_TAXONOMY = ROOT / "data/children/taxonomy.json"
CHILD_ART = ROOT / "scripts/generate_children_artwork.py"
CHILD_ART_WF = ROOT / ".github/workflows/generate-animated-children-stories.yml"
MASTER_GOVERNANCE = ROOT / "scripts/check_master_governance.py"
MASTER_GOVERNANCE_WF = ROOT / ".github/workflows/master-governance.yml"
SOURCE_POLICIES = [
    ROOT / "CONTENT_SOURCE_POLICY.md",
    ROOT / "EDITORIAL-GENUINE-SOURCE-POLICY.md",
]
PROCESS_DECLARATION = "GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md"
REQUIRED_CHILD_TYPES = {
    "verified-readings",
    "illustrated-stories",
    "very-short-stories",
    "animated-stories",
    "media",
}


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> int:
    errors: list[str] = []
    required_files = [
        MASTER,
        BASE,
        README,
        CHILD_TAXONOMY,
        CHILD_ART,
        CHILD_ART_WF,
        MASTER_GOVERNANCE,
        MASTER_GOVERNANCE_WF,
        *SOURCE_POLICIES,
    ]
    for path in required_files:
        if not path.is_file():
            fail(errors, f"missing required file: {path.relative_to(ROOT)}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    master = read_text(MASTER)
    if "ar-MA" not in master or "MASTER-OVERRIDING-SITE-INSTRUCTION-BASE.md" not in master:
        fail(errors, "canonical master must incorporate the base and govern Arabic audio with ar-MA")

    readme = read_text(README)
    if "MASTER-OVERRIDING-SITE-INSTRUCTION.md" not in readme:
        fail(errors, "README does not identify the canonical master instruction")

    taxonomy = json.loads(read_text(CHILD_TAXONOMY))
    if taxonomy.get("sectionLabelAr") != "أحباب الله":
        fail(errors, "children section must be labelled أحباب الله")

    child_types = taxonomy.get("contentTypes") or []
    child_type_ids = {item.get("id") for item in child_types}
    missing_types = sorted(REQUIRED_CHILD_TYPES - child_type_ids)
    if missing_types:
        fail(errors, f"children taxonomy missing content types: {', '.join(missing_types)}")

    for group_name in ("contentTypes", "subjects"):
        for i, item in enumerate(taxonomy.get(group_name) or []):
            missing = [key for key in ("labelAr", "labelEn", "labelFr") if not item.get(key)]
            if missing:
                fail(errors, f"{group_name}[{i}] missing trilingual labels: {', '.join(missing)}")

    if len(taxonomy.get("ageGroups") or []) < 1:
        fail(errors, "children taxonomy has no age groups")

    art = read_text(CHILD_ART)
    for token in (
        PROCESS_DECLARATION,
        "OPENAI_API_KEY",
        "gpt-image-2",
        "replacementArtwork",
        "source",
        "DO NOT depict",
    ):
        if token not in art:
            fail(errors, f"children artwork generator missing safeguard/capability token: {token}")

    art_wf = read_text(CHILD_ART_WF)
    for token in (
        PROCESS_DECLARATION,
        "OPENAI_API_KEY",
        "scripts/generate_children_artwork.py",
        "contents: write",
    ):
        if token not in art_wf:
            fail(errors, f"children artwork workflow missing required token: {token}")

    for path in (MASTER_GOVERNANCE, MASTER_GOVERNANCE_WF):
        if PROCESS_DECLARATION not in read_text(path):
            fail(errors, f"critical governance process has stale declaration: {path.relative_to(ROOT)}")

    policy_text = "\n".join(read_text(path) for path in SOURCE_POLICIES)
    if not re.search(r"source|provenance|evidence", policy_text, flags=re.I):
        fail(errors, "source policies do not visibly enforce source/provenance evidence")

    # Reject configured ar-SA in runtime-oriented web/data/config files. Markdown
    # governance prose and migration/audit scripts are intentionally excluded.
    runtime_suffixes = {".html", ".js", ".mjs", ".cjs", ".json", ".webmanifest", ".toml", ".ini", ".cfg"}
    excluded_roots = {".git", "node_modules", "vendor", "dist", "build", "runtime_cache"}
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in runtime_suffixes:
            continue
        rel = path.relative_to(ROOT)
        if any(part in excluded_roots for part in rel.parts):
            continue
        try:
            text = read_text(path)
        except UnicodeDecodeError:
            continue
        if "ar-SA" in text:
            fail(errors, f"configured/runtime ar-SA remains; migrate to ar-MA: {rel}")

    if errors:
        print(f"CURRENT-INSTRUCTIONS AUDIT FAIL ({len(errors)} defect(s))", file=sys.stderr)
        for error in errors:
            print(f" - {error}", file=sys.stderr)
        return 1

    print("CURRENT-INSTRUCTIONS AUDIT PASS")
    print(f"children content types: {len(child_types)}")
    print(f"children subjects: {len(taxonomy.get('subjects') or [])}")
    print(f"children age groups: {len(taxonomy.get('ageGroups') or [])}")
    print("canonical governance: PASS")
    print("trilingual children taxonomy: PASS")
    print("children replacement artwork pipeline: PASS")
    print("source/provenance policy presence: PASS")
    print("runtime ar-MA enforcement: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
