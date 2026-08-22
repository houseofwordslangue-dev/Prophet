#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations
import json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
AVAIL=ROOT/'data/editorial/resource_extraction_availability.json'
QUEUE=ROOT/'private/resource_extraction_queue.json'
OUT=ROOT/'data/editorial/extraction_ready_sources.json'
GATE=ROOT/'data/editorial/resource_extraction_gate.json'

def load(p,d):
    try:return json.loads(p.read_text(encoding='utf-8'))
    except Exception:return d

def save(p,o):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    a=load(AVAIL,{}) or {}; q=load(QUEUE,{}) or {}
    rows=[x for x in a.get('items',[]) if isinstance(x,dict)]
    ready=[x for x in rows if x.get('extractionReady') and isinstance(x.get('preferred'),dict) and x['preferred'].get('url')]
    blocked=[x for x in rows if not x.get('extractionReady')]
    manifest=[]
    for x in ready:
        p=x['preferred']
        manifest.append({
            'id':x.get('id'),'title':x.get('title'),'author':x.get('author'),
            'state':x.get('state'),'format':p.get('format'),'url':p.get('url'),
            'driveId':p.get('driveId'),'source':p.get('source'),'textOrigin':p.get('textOrigin'),
            'ocrDerived':bool(x.get('ocrDerived')),'verifiedAccessible':bool(p.get('verifiedAccessible',True)),
            'generationEligible':True,
            'rule':'Generation/extraction may use this resource only through the recorded preferred extraction path; preserve provenance.'
        })
    stamp=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
    save(OUT,{'schema':'extraction-ready-sources-v1','generatedAt':stamp,'count':len(manifest),'items':manifest})
    save(GATE,{
        'schema':'resource-extraction-gate-v1','generatedAt':stamp,
        'cataloguedResources':len(rows),'extractionReady':len(ready),'acquisitionRequired':len(blocked),
        'coveragePercent':round((100*len(ready)/len(rows)),2) if rows else 0,
        'queueCount':len(q.get('items',[])) if isinstance(q,dict) else len(blocked),
        'generationPolicy':'Use ONLY data/editorial/extraction_ready_sources.json as the source pool for automated extraction/generation. Blocked resources stay in acquisition/review and are retried; they must not be cited as extracted sources until a real extraction path exists.',
        'allResourcesExtractionReady':bool(rows) and not blocked,
        'status':'READY_ALL' if rows and not blocked else 'PARTIAL_RECOVERY_REQUIRED'
    })
    print(json.dumps({'catalogued':len(rows),'ready':len(ready),'blocked':len(blocked),'coveragePercent':round((100*len(ready)/len(rows)),2) if rows else 0},ensure_ascii=False))
if __name__=='__main__':main()
