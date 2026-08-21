#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'
OUT=DATA/'production_manifest_all.generated.json'

TECH_KEYS={'logs','status','chunks','cache','temporary','diagnostic'}

def load(path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return None

def rows(obj):
    if isinstance(obj,dict):
        for key in ('items','articles','records','sources','people','biographies','researches','documents','media'):
            val=obj.get(key)
            if isinstance(val,list):
                return val
    return []

def rid(x,src,i):
    if isinstance(x,dict):
        for k in ('id','workId','slug','articleId','personId','mediaId'):
            if x.get(k): return str(x[k])
    return f'{src}:{i}'

def is_publishable_record(x):
    if not isinstance(x,dict): return False
    status=' '.join(str(x.get(k,'')) for k in ('lifecycleStatus','publicationStatus','status')).lower()
    if any(v in status for v in ('draft','private','rejected','failed')): return False
    if x.get('publishedAsset') is False: return False
    return True

def main():
    registries=[]; uniq={}; hashes={}
    for path in sorted(DATA.rglob('*.json')):
        rel=path.relative_to(ROOT).as_posix()
        if path.name in {OUT.name}: continue
        obj=load(path)
        if obj is None: continue
        rs=rows(obj)
        if not rs: continue
        pub=0
        for i,x in enumerate(rs):
            if not is_publishable_record(x): continue
            ident=rid(x,rel,i); sha=str(x.get('sha256','')) if isinstance(x,dict) else ''
            key=('sha:'+sha) if sha and sha in hashes else ('id:'+ident)
            if sha and sha not in hashes: hashes[sha]=ident
            if key not in uniq:
                uniq[key]={'id':ident,'registry':rel,'kind':str(x.get('kind') or x.get('type') or x.get('format') or 'record') if isinstance(x,dict) else 'record'}
            pub+=1
        registries.append({'path':rel,'records':len(rs),'publishableRecords':pub})
    drive=load(DATA/'drive_production_manifest.json') or {}
    drive_count=int(drive.get('count',0) or 0)
    # Drive folder manifest is authoritative for work-level Drive publishing; OCR/text/volume derivatives stay attached to parents.
    result={
      'schema':'prophet-production-reconciliation-v1',
      'generatedAt':datetime.now(timezone.utc).isoformat(),
      'publicationPolicy':'REAL_ASSETS_ONLY_NO_FAKE_CAPABILITIES',
      'githubRegistryCount':len(registries),
      'githubPublishableRecordCount':len(uniq),
      'drivePublishedWorkCount':drive_count,
      'dropboxPublishedWorkCount':0,
      'registries':registries,
      'records':list(uniq.values()),
      'assetPolicy':{'derivativesAttachToParent':True,'technicalArtifactsAreNotStandaloneCatalogueWorks':True}
    }
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'output':str(OUT.relative_to(ROOT)),'github':len(uniq),'drive':drive_count},ensure_ascii=False))

if __name__=='__main__': main()
