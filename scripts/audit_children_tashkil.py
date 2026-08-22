#!/usr/bin/env python3
"""Mandatory Arabic diacritics gate for child-facing files.

Internal search keys/keywords/IDs are exempt. Public Arabic strings must carry Arabic
combining marks; failures are emitted as FAIL_TASHKIL and produce a non-zero exit.
This is a conservative gate: it detects missing vocalization, not linguistic correctness.
"""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AR = re.compile(r"[\u0621-\u064A\u066E-\u06D3]")
DIAC = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")
HTML_TEXT = re.compile(r">([^<>]+)<")
QUOTED = re.compile(r"(['\"])(.*?)(?<!\\)\1")
EXEMPT_KEYS = {"keywords", "searchAr", "searchTextAr", "normalizedAr", "id", "href", "path", "url"}
FILES = [
    ROOT / "children.html",
    ROOT / "children-stories.html",
    ROOT / "children-very-short.html",
    ROOT / "children-animated.html",
    ROOT / "children-videos.html",
    ROOT / "assets" / "children-1200.js",
    ROOT / "assets" / "children-hub.js",
    ROOT / "data" / "children" / "taxonomy.json",
    ROOT / "data" / "children" / "story-seeds.json",
]

def has_arabic(s: str) -> bool: return bool(AR.search(s))
def has_diac(s: str) -> bool: return bool(DIAC.search(s))
def ratio(s: str) -> float:
    letters=len(AR.findall(s)); marks=len(DIAC.findall(s)); return marks/letters if letters else 1.0

def inspect_json(obj, where="$"):
    failures=[]
    if isinstance(obj, dict):
        for k,v in obj.items():
            if k in EXEMPT_KEYS or k.lower().startswith("search") or k.lower().endswith("keywords"):
                continue
            failures += inspect_json(v, f"{where}.{k}")
    elif isinstance(obj, list):
        for i,v in enumerate(obj): failures += inspect_json(v, f"{where}[{i}]")
    elif isinstance(obj, str) and has_arabic(obj) and not has_diac(obj):
        failures.append({"location":where,"text":obj[:180],"status":"FAIL_TASHKIL"})
    return failures

def inspect_file(path: Path):
    if not path.exists(): return [{"file":str(path.relative_to(ROOT)),"status":"MISSING"}]
    text=path.read_text(encoding="utf-8")
    if path.suffix==".json":
        rows=inspect_json(json.loads(text))
    else:
        candidates=[]
        if path.suffix==".html": candidates += [x.strip() for x in HTML_TEXT.findall(text)]
        candidates += [m.group(2) for m in QUOTED.finditer(text)]
        rows=[]
        for s in candidates:
            if not has_arabic(s): continue
            # Ignore regex/source-code fragments and deliberately normalized search data.
            if "\\u" in s or "children|kids" in s or "اطفال|طفل" in s: continue
            if not has_diac(s): rows.append({"text":s[:180],"status":"FAIL_TASHKIL"})
    return [{"file":str(path.relative_to(ROOT)),**r} for r in rows]

def main():
    failures=[]
    for path in FILES: failures += inspect_file(path)
    report={
      "schema":"children-tashkil-gate-v1",
      "policy":"child-facing Arabic must be vocalized; normalized search metadata exempt",
      "filesChecked":[str(p.relative_to(ROOT)) for p in FILES],
      "failureCount":len(failures),
      "failures":failures,
      "status":"PASS" if not failures else "FAIL_TASHKIL"
    }
    out=ROOT/"data"/"children"/"editorial"/"tashkil_audit.json";out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
    raise SystemExit(0 if not failures else 1)
if __name__=="__main__": main()
