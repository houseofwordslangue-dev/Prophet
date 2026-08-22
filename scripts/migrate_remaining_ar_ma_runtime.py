#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FILES=[
 'assets/prophet-bookreader.js',
 'assets/bookstore.js',
 'assets/children-animated.js',
 'assets/reader-futurist.js',
 'assets/children-very-short.js',
]
changed=[]
for rel in FILES:
 p=ROOT/rel
 if not p.exists():
  raise SystemExit(f'missing runtime file: {rel}')
 s=p.read_text(encoding='utf-8')
 n=s.count('ar-SA')
 if n:
  p.write_text(s.replace('ar-SA','ar-MA'),encoding='utf-8')
  changed.append((rel,n))
print('ar-MA runtime migration:', changed or 'already clean')
