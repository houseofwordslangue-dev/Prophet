#!/usr/bin/env python3
"""GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
Deterministic acceptance audit for the unified controlling instruction.
"""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]
SELF=Path(__file__).resolve()
M=ROOT/"MASTER-OVERRIDING-SITE-INSTRUCTION.md"
D="GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md"
STALE="GOVERNED_BY: MASTER_"+"OVERRIDING_INSTRUCTION.md"
def main():
 e=[]
 if not M.is_file():e.append("missing canonical master")
 else:
  s=M.read_text(encoding="utf-8")
  for x in ("1. PRIMARY OBJECTIVE","88.","101.","102. SINGLE-FILE MASTER AUTHORITY","103. CANONICAL","الأسرة النبوية","العائلة النبوية","104. CANONICAL SOURCES AND STUDIES","105. GLOBAL ARABIC SPEECH","106. CROSS-SESSION / REPOSITORY / DRIVE RECONCILIATION RULE","END OF MASTER OVERRIDING INSTRUCTION"):
   if x not in s:e.append("master missing marker: "+x)
  if len(s)<65000:e.append("canonical master is unexpectedly short")
  if "incorporated into this canonical master instruction by reference" in s:e.append("canonical master still uses incorporated-by-reference split authority")
  if "Do not maintain a competing top-level `العائلة النبوية` architecture" in s:e.append("master still collapses العائلة النبوية into الأسرة النبوية")
 if (ROOT/"MASTER-OVERRIDING-SITE-INSTRUCTION-BASE.md").exists():e.append("split BASE master still exists")
 alias=ROOT/"MASTER_OVERRIDING_INSTRUCTION.md"
 if alias.exists():
  a=alias.read_text(encoding="utf-8")
  if "sole authoritative project instruction" not in a or "MASTER-OVERRIDING-SITE-INSTRUCTION.md" not in a:e.append("underscore master alias still claims authority")
 menu=(ROOT/"assets/site-menu.js").read_text(encoding="utf-8")
 for x in ("الأسرة النبوية","الزوجات / أمهات المؤمنين","family.html?group=wives","العائلة النبوية","family.html?group=parents","family.html?group=ancestors","المصادر والدراسات","المقالات والموضوعات"):
  if x not in menu:e.append("menu missing: "+x)
 if "loadChildrenChat()" in menu:e.append("duplicate child assistant loader remains")
 fam=(ROOT/"assets/family.js").read_text(encoding="utf-8")
 for x in ("requestedGroup=P.get('group')","'wives'","groupMatches","pid=p?.id||x.id"):
  if x not in fam:e.append("family canonical routing missing: "+x)
 tax=json.loads((ROOT/"data/content_taxonomy_policy.json").read_text(encoding="utf-8"))
 cs=tax.get("canonicalSections",{})
 if cs.get("family",{}).get("groups")!=["wives","children","grandchildren"]:e.append("الأسرة النبوية scope mismatch")
 if cs.get("family",{}).get("wivesLabelAr")!="الزوجات / أمهات المؤمنين":e.append("taxonomy missing wives collection")
 if cs.get("extendedFamily",{}).get("labelAr")!="العائلة النبوية":e.append("taxonomy missing independent العائلة النبوية")
 if cs.get("extendedFamily",{}).get("groups")!=["parents","ancestors","paternal-relatives","maternal-relatives","cousins","in-laws","foster","family-tree"]:e.append("العائلة النبوية scope mismatch")
 if cs.get("library",{}).get("labelAr")!="المصادر والدراسات":e.append("taxonomy library label mismatch")
 for q in (ROOT/"scripts").rglob("*"):
  if not q.is_file() or q.suffix.lower() not in {".py",".js",".mjs",".cjs",".sh",".ts"}:continue
  try:t=q.read_text(encoding="utf-8")
  except UnicodeDecodeError:continue
  if D not in t:e.append("script lacks canonical declaration: "+str(q.relative_to(ROOT)))
  if q.resolve()!=SELF and STALE in t:e.append("stale governing alias: "+str(q.relative_to(ROOT)))
 for q in (ROOT/".github/workflows").glob("*.y*"):
  try:t=q.read_text(encoding="utf-8")
  except UnicodeDecodeError:continue
  if STALE in t:e.append("workflow uses stale governing alias: "+str(q.relative_to(ROOT)))
 for q in ROOT.rglob("*"):
  if not q.is_file() or q.suffix.lower() not in {".html",".js",".mjs",".cjs",".json",".webmanifest",".toml",".ini",".cfg"}:continue
  if any(x in q.parts for x in (".git","node_modules","vendor","dist","build","runtime_cache")):continue
  try:t=q.read_text(encoding="utf-8")
  except UnicodeDecodeError:continue
  if "ar-SA" in t:e.append("configured runtime ar-SA: "+str(q.relative_to(ROOT)))
 if e:
  print("CURRENT-INSTRUCTIONS AUDIT FAIL",file=sys.stderr);[print(" - "+x,file=sys.stderr) for x in e];return 1
 print("CURRENT-INSTRUCTIONS AUDIT PASS");return 0
if __name__=="__main__":raise SystemExit(main())
