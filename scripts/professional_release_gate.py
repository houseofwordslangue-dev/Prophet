#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
CRITICAL_PAGES=[ROOT/x for x in ('library.html','library-all.html','media.html','children.html','children-stories.html','children-very-short.html','children-animated.html','children-videos.html','people.html','person.html','family.html')]
MAX_HTML_BYTES=180_000
MAX_STYLESHEETS=18
MAX_SCRIPTS=20

def main():
    errors=[];warnings=[]
    for page in CRITICAL_PAGES:
        if not page.exists():errors.append(f'missing critical page: {page.name}');continue
        text=page.read_text(encoding='utf-8');size=page.stat().st_size
        if size>MAX_HTML_BYTES:warnings.append(f'{page.name}: HTML exceeds preferred {MAX_HTML_BYTES} bytes ({size})')
        styles=re.findall(r'<link\b[^>]*rel=["\']stylesheet["\'][^>]*>',text,flags=re.I)
        scripts=re.findall(r'<script\b[^>]*src=["\'][^"\']+["\'][^>]*>',text,flags=re.I)
        if len(styles)>MAX_STYLESHEETS:warnings.append(f'{page.name}: stylesheet count {len(styles)} > {MAX_STYLESHEETS}')
        if len(scripts)>MAX_SCRIPTS:warnings.append(f'{page.name}: script count {len(scripts)} > {MAX_SCRIPTS}')
        for tag in scripts:
            if not re.search(r'\b(?:defer|async|type=["\']module["\'])\b',tag,flags=re.I):warnings.append(f'{page.name}: parser-blocking external script: {tag[:180]}')
        if re.search(r'\bjavascript\s*:',text,flags=re.I):errors.append(f'{page.name}: javascript: URL detected')
        insecure=re.findall(r'(?:src|href)=["\']http://[^"\']+',text,flags=re.I)
        if insecure:errors.append(f'{page.name}: insecure HTTP asset/link detected')
    print('PROFESSIONAL RELEASE GATE:', 'FAIL' if errors else 'PASS')
    for x in errors:print('- HARD:',x)
    for x in warnings:print('- REVIEW:',x)
    # Performance-budget findings are diagnostics; unsafe javascript/http or missing critical pages are hard.
    return 1 if errors else 0
if __name__=='__main__':raise SystemExit(main())
