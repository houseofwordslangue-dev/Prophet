#!/usr/bin/env python3
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
CRITICAL_PAGES = [ROOT / "library.html", ROOT / "media.html"]
MAX_HTML_BYTES = 120_000
MAX_STYLESHEETS = 14
MAX_SCRIPTS = 16

errors = []

for page in CRITICAL_PAGES:
    if not page.exists():
        errors.append(f"missing critical page: {page.name}")
        continue
    text = page.read_text(encoding="utf-8")
    size = page.stat().st_size
    if size > MAX_HTML_BYTES:
        errors.append(f"{page.name}: HTML exceeds {MAX_HTML_BYTES} bytes ({size})")

    styles = re.findall(r'<link\b[^>]*rel=["\']stylesheet["\'][^>]*>', text, flags=re.I)
    scripts = re.findall(r'<script\b[^>]*src=["\'][^"\']+["\'][^>]*>', text, flags=re.I)
    if len(styles) > MAX_STYLESHEETS:
        errors.append(f"{page.name}: too many stylesheets ({len(styles)} > {MAX_STYLESHEETS})")
    if len(scripts) > MAX_SCRIPTS:
        errors.append(f"{page.name}: too many scripts ({len(scripts)} > {MAX_SCRIPTS})")

    for tag in scripts:
        if not re.search(r'\b(?:defer|async)\b', tag, flags=re.I):
            errors.append(f"{page.name}: parser-blocking script: {tag}")

    if re.search(r'\bjavascript\s*:', text, flags=re.I):
        errors.append(f"{page.name}: javascript: URL detected")

    insecure = re.findall(r'(?:src|href)=["\']http://[^"\']+', text, flags=re.I)
    if insecure:
        errors.append(f"{page.name}: insecure HTTP asset/link detected")

if errors:
    print("PROFESSIONAL RELEASE GATE: FAIL")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("PROFESSIONAL RELEASE GATE: PASS")
print("- critical HTML size budgets passed")
print("- stylesheet/script count budgets passed")
print("- critical scripts are non-parser-blocking")
print("- no javascript: URLs or insecure HTTP assets on critical pages")
