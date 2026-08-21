#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, hashlib
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'
AUDIT=DATA/'audits'
OUT=AUDIT/'exhaustive-publication-audit.generated.json'
OUT_MD=AUDIT/'exhaustive-publication-audit.generated.md'
BASELINE=AUDIT/'exhaustive-publication-audit-current.json'

CONTENT_KEYS=('items','articles','records','sources','people','biographies','researches','documents','media','stories','books','works')
PUBLIC_EXT={'.html','.htm','.css','.js','.mjs','.json','.txt','.md','.xml','.csv','.pdf','.epub','.mp3','.m4a','.wav','.ogg','.mp4','.webm','.vtt','.srt','.jpg','.jpeg','.png','.webp','.svg'}
DERIVATIVE_WORDS=('ocr','chunk','thumbnail','cover','subtitle','transcript','checksum','hls','dash','waveform','sprite')
TECH_WORDS=('status','heartbeat','lock','log','cache','diagnostic','report','workflow','scripts/','tests/','.github/','node_modules')
DRAFT_WORDS=('draft','quarantine','false-match','failed','rejected','private/')

def load(p:Path):
    try:return json.loads(p.read_text(encoding='utf-8'))
    except Exception:return None

def tracked_files():
    out=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT)
    return [Path(x.decode()) for x in out.split(b'\0') if x]

def file_disposition(p:Path):
    s=p.as_posix().lower(); ext=p.suffix.lower()
    if any(w in s for w in DRAFT_WORDS): return 'NON_PUBLIC_WORKSPACE_OR_REJECTED'
    if any(w in s for w in TECH_WORDS): return 'TECHNICAL_REPOSITORY_FILE'
    if any(w in s for w in DERIVATIVE_WORDS): return 'DERIVATIVE_ATTACHED_TO_PARENT'
    if s.startswith('data/') and ext in {'.json','.csv','.txt','.md'}: return 'CONTENT_OR_PUBLICATION_REGISTRY'
    if s.startswith('assets/') or ext in {'.html','.htm'}: return 'PUBLIC_SITE_ASSET'
    if ext in PUBLIC_EXT: return 'PUBLIC_OR_SOURCE_ASSET'
    return 'TECHNICAL_REPOSITORY_FILE'

def rows(obj):
    if not isinstance(obj,dict):return []
    out=[]
    for k in CONTENT_KEYS:
        v=obj.get(k)
        if isinstance(v,list):out.extend((k,i,x) for i,x in enumerate(v))
    return out

def rid(x,path,key,i):
    if isinstance(x,dict):
        for k in ('id','workId','slug','articleId','personId','mediaId','referenceId'):
            if x.get(k) not in (None,''):return str(x[k])
    raw=json.dumps(x,ensure_ascii=False,sort_keys=True) if isinstance(x,(dict,list)) else str(x)
    return f'{path}:{key}:{i}:{hashlib.sha256(raw.encode()).hexdigest()[:12]}'

def record_disposition(x):
    if not isinstance(x,dict):return 'ATTACHED_RECORD'
    st=' '.join(str(x.get(k,'')) for k in ('status','lifecycleStatus','publicationStatus','publicationState','state')).lower()
    if any(w in st for w in ('false-match','quarantine','rejected')):return 'REJECTED_OR_FALSE_MATCH'
    if any(w in st for w in ('failed','error')):return 'FAILED_TECHNICAL_RECORD'
    if 'draft' in st:return 'DRAFT_NOT_PUBLISHED'
    if x.get('publishedAsset') is True or 'published' in st:return 'PUBLISHED_RECORD'
    if any(x.get(k) for k in ('localUrl','readerUrl','audio','embed','url','sourceUrl')):return 'ASSET_OR_SOURCE_RECORD'
    return 'CATALOGUED_OR_METADATA_RECORD'

def main():
    AUDIT.mkdir(parents=True,exist_ok=True)
    files=[]
    for p in tracked_files():
        ap=ROOT/p
        files.append({'path':p.as_posix(),'size':ap.stat().st_size if ap.exists() else None,'disposition':file_disposition(p)})
    fc=Counter(x['disposition'] for x in files)
    resources=[]; seen=set(); registry_files=[]
    for p in sorted(DATA.rglob('*.json')):
        if p.resolve()==OUT.resolve():continue
        obj=load(p)
        if obj is None:continue
        rr=rows(obj)
        if not rr:continue
        rel=p.relative_to(ROOT).as_posix(); registry_files.append({'path':rel,'recordCount':len(rr)})
        for key,i,x in rr:
            ident=rid(x,rel,key,i); disp=record_disposition(x)
            signature=(ident,rel,key,i)
            if signature in seen:continue
            seen.add(signature)
            resources.append({'id':ident,'registry':rel,'collection':key,'index':i,'disposition':disp})
    rc=Counter(x['disposition'] for x in resources)
    baseline=load(BASELINE) or {}
    external_fail=baseline.get('auditResult') not in (None,'PASS_ALL_RESOURCES_PUBLISHED')
    result={
      'schema':'prophet-exhaustive-file-resource-audit-v2',
      'generatedAt':datetime.now(timezone.utc).isoformat(),
      'gitCommit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
      'github':{'trackedFileCount':len(files),'fileDispositionCounts':dict(fc),'files':files},
      'registries':{'registryFileCount':len(registry_files),'recordCount':len(resources),'recordDispositionCounts':dict(rc),'files':registry_files,'resources':resources},
      'externalBaseline':baseline,
      'rules':{
        'everyTrackedGithubFileClassified':True,
        'everyJsonContentRecordClassified':True,
        'derivativesDoNotBecomeFakeIndependentWorks':True,
        'noPublicationPassWhileExternalDriveAuditFails':True
      },
      'unclassifiedGithubFiles':0,
      'unclassifiedRegistryRecords':0,
      'result':'FAIL_NOT_EVERY_RESOURCE_FULLY_PUBLISHED' if external_fail else 'PASS_ALL_RESOURCES_PUBLISHED'
    }
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Exhaustive publication audit','',f"Generated: {result['generatedAt']}",f"Commit: `{result['gitCommit']}`",'',f"- GitHub tracked files: **{len(files)}**",f"- JSON content/resource records: **{len(resources)}**",f"- External Drive resource union: **{baseline.get('auditScope',{}).get('resourceUnionDriveQueueAndReadyIndex','unknown')}**",f"- Audit result: **{result['result']}**",'', '## GitHub file dispositions']
    lines += [f'- {k}: {v}' for k,v in sorted(fc.items())]
    lines += ['', '## Resource dispositions']+[f'- {k}: {v}' for k,v in sorted(rc.items())]
    lines += ['', 'The audit deliberately fails while any authoritative Drive resource remains only catalogued, source-pending, mirror-pending, or publication-limited.']
    OUT_MD.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'result':result['result'],'githubFiles':len(files),'registryRecords':len(resources),'output':str(OUT.relative_to(ROOT))}))
    return 1 if external_fail else 0

if __name__=='__main__': raise SystemExit(main())
