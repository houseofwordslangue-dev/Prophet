#!/usr/bin/env python3
"""GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
Deterministic acceptance audit for the unified controlling instruction.
"""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]
M=ROOT/"MASTER-OVERRIDING-SITE-INSTRUCTION.md"
D="GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md"
def main():
 e=[]
 if not M.is_file():e.append("missing canonical master")
 else:
  s=M.read_text(encoding="utf-8")
  for x in ("1. PRIMARY OBJECTIVE","88.","101.","102. SINGLE-FILE MASTER AUTHORITY","103. CANONICAL FAMILY NAVIGATION","104. CANONICAL SOURCES AND STUDIES","105. GLOBAL ARABIC SPEECH","106. CROSS-SESSION / REPOSITORY / DRIVE RECONCILIATION RULE","END OF MASTER OVERRIDING INSTRUCTION"):
   if x not in s:e.append("master missing marker: "+x)
  if len(s)<65000:e.append("canonical master is unexpectedly short")
  if "MASTER-OVERRIDING-SITE-INSTRUCTION-BASE.md" in s:e.append("canonical master still depends on split BASE")
 if (ROOT/"MASTER-OVERRIDING-SITE-INSTRUCTION-BASE.md").exists():e.append("split BASE master still exists")
 menu=(ROOT/"assets/site-menu.js").read_text(encoding="utf-8")
 for x in ("الزوجات / أمهات المؤمنين","family.html?group=wives","المصادر والدراسات","المقالات والموضوعات"):
  if x not in menu:e.append("menu missing: "+x)
 if "['العائلة النبوية'" in menu:e.append("competing top-level family taxonomy remains")
 if "loadChildrenChat()" in menu:e.append("duplicate child assistant loader remains")
 fam=(ROOT/"assets/family.js").read_text(encoding="utf-8")
 for x in ("requestedGroup=P.get('group')","'wives'","groupMatches"):
  if x not in fam:e.append("family routing missing: "+x)
 tax=json.loads((ROOT/"data/content_taxonomy_policy.json").read_text(encoding="utf-8"))
 cs=tax.get("canonicalSections",{})
 if cs.get("family",{}).get("wivesLabelAr")!="الزوجات / أمهات المؤمنين":e.append("taxonomy missing wives collection")
 if cs.get("library",{}).get("labelAr")!="المصادر والدراسات":e.append("taxonomy library label mismatch")
 for root in (ROOT/"scripts",):
  for q in root.rglob("*"):
   if not q.is_file() or q.suffix.lower() not in {".yml",".yaml",".py",".js",".mjs",".cjs",".sh",".ts"}:continue
   try:t=q.read_text(encoding="utf-8")
   except UnicodeDecodeError:continue
   if D not in t:e.append("process lacks canonical declaration: "+str(q.relative_to(ROOT)))
   if "GOVERNED_BY: MASTER_OVERRIDING_INSTRUCTION.md" in t:e.append("stale governing alias: "+str(q.relative_to(ROOT)))
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
