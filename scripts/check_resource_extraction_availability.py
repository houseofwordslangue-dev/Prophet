#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
AVAIL=ROOT/'data'/'editorial'/'resource_extraction_availability.json'
QUEUE=ROOT/'private'/'resource_extraction_queue.json'
RES=ROOT/'private'/'source_first_resolution.json'

def load(p,d):
    try:return json.loads(p.read_text(encoding='utf-8'))
    except Exception:return d

def main():
    a=load(AVAIL,{})
    r=load(RES,{})
    q=load(QUEUE,{})
    total=int(a.get('catalogResources') or r.get('catalogResources') or 0)
    ready=int(a.get('extractionReady') or r.get('extractionReady') or 0)
    unresolved=int(a.get('acquisitionRequired') or r.get('acquisitionRequired') or len(q.get('items',[])))
    print(json.dumps({
        'catalogResources':total,
        'extractionReady':ready,
        'acquisitionRequired':unresolved,
        'coveragePercent':a.get('coveragePercent'),
        'generationPolicy':'ONLY extractionReady=true resources may feed extraction/generation',
        'allResourcesExtractionReady':unresolved==0
    },ensure_ascii=False))
    # This is a strict availability gate for claims of 100% readiness. It deliberately
    # does not delete or suppress unresolved resources: they stay in acquisition queue.
    return 0 if unresolved==0 else 2

if __name__=='__main__':sys.exit(main())
