#!/usr/bin/env python3
from __future__ import annotations

import json, re, shutil, hashlib
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'; EDIT=DATA/'editorial'; DRAFTS=EDIT/'drafts'
OUT_DIR=EDIT/'short-biography-extensions'
INDEX=EDIT/'short_biography_extensions.json'
AUDIT=EDIT/'short_biographies_500_audit.json'
TARGET=500
AR=re.compile(r'[\u0600-\u06ff]')
DIAC=re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06EDـ]')

def now(): return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def read(p,default=None):
    try:return json.loads(p.read_text(encoding='utf-8'))
    except Exception:return default

def norm(s):
    s=DIAC.sub('',str(s or '')).replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي')
    return re.sub(r'\s+',' ',s).strip()
def wc(s): return len(re.findall(r'\S+',re.sub(r'\s+',' ',str(s or '')).strip()))
def arabic_enough(s):
    s=str(s or ''); a=len(AR.findall(s)); return a>=80 and a>=max(80,len(s)//5)
def fp(s): return hashlib.sha256(norm(s).encode()).hexdigest()
def safe_id(s): return re.sub(r'[^A-Za-z0-9._-]+','-',str(s)).strip('-') or 'person'

def rows(payload):
    if isinstance(payload,list): return payload
    if isinstance(payload,dict):
        for k in ('people','registry','items','records','drafts','biographies','entries','repairs'):
            if isinstance(payload.get(k),list): return payload[k]
    return []

def person_id(row):
    if not isinstance(row,dict): return None
    for k in ('canonicalPersonId','personId','subjectPerson'):
        if row.get(k): return str(row[k])
    for k in ('relatedPerson','subject'):
        x=row.get(k)
        if isinstance(x,dict) and x.get('id'): return str(x['id'])
    return None

def source_backed(row):
    if not isinstance(row,dict): return False
    if any(row.get(k) for k in ('sources','sourceRefs','references','provenance','source','sourceKey')): return True
    blob=' '.join(str(row.get(k) or '') for k in ('contentType','draftStatus','publicationStatus','sourceType')).upper()
    return any(x in blob for x in ('SOURCE','VERIFIED','EXTRACT','OCR','TRANSCR'))

def texts_from(obj, depth=0):
    if depth>5:return []
    out=[]
    if isinstance(obj,str):
        if arabic_enough(obj): out.append(re.sub(r'\s+',' ',obj).strip())
    elif isinstance(obj,list):
        for x in obj: out.extend(texts_from(x,depth+1))
    elif isinstance(obj,dict):
        preferred=('biography','bio','bodyAr','summaryAr','descriptionAr','contentAr','textAr','articleBody','body','content','text','paragraphs','sourcePassages','passages','chapters')
        for k in preferred:
            if k in obj: out.extend(texts_from(obj[k],depth+1))
    return out

def collect_people():
    people={}
    for path,key in [
        (DATA/'people.json','people'),(DATA/'family_people.json','people'),(DATA/'family_groups.json','registry'),
        (DATA/'family_biographies.json','people'),(DATA/'expanded_people_135.json','people')]:
        p=read(path,{}) or {}
        seq=p.get(key,[]) if isinstance(p,dict) else []
        for r in seq:
            if not isinstance(r,dict) or not r.get('id'): continue
            pid=str(r['id']); n=r.get('nameAr') or ((r.get('name') or {}).get('ar') if isinstance(r.get('name'),dict) else None)
            if not n: continue
            people.setdefault(pid,{'id':pid,'nameAr':str(n),'category':r.get('category') or ''})
    return people

def add_text(bucket, seen, pid, text, source, kind):
    if not text or not arabic_enough(text): return
    key=fp(text)
    if key in seen[pid]: return
    seen[pid].add(key); bucket[pid].append({'text':text,'wordCount':wc(text),'source':source,'kind':kind})

def main():
    people=collect_people(); baseline=defaultdict(list); seen=defaultdict(set)

    # Canonical/person datasets count only exact-id owned Arabic text.
    canonical_files=[DATA/'people.json',DATA/'family_people.json',DATA/'family_groups.json',DATA/'family_biographies.json',
                     DATA/'expanded_biographies_135_full.json',EDIT/'canonical_biographies.json',EDIT/'biography_repairs_20260821.json']
    for path in canonical_files:
        p=read(path,{})
        for r in rows(p):
            if not isinstance(r,dict): continue
            pid=str(r.get('id') or r.get('personId') or r.get('canonicalPersonId') or '')
            if pid not in people: continue
            for t in texts_from(r): add_text(baseline,seen,pid,t,{'repositoryPath':str(path.relative_to(ROOT))},'canonical')

    # Existing strict life chapters and source extensions are direct-owned evidence.
    for folder in (EDIT/'canonical-life', EDIT/'biography-extensions'):
        if not folder.exists(): continue
        for path in folder.glob('*.json'):
            p=read(path,{}) or {}; pid=str(p.get('personId') or '')
            if pid not in people: continue
            for t in texts_from(p): add_text(baseline,seen,pid,t,{'repositoryPath':str(path.relative_to(ROOT))},'existing-direct-extension')

    before={pid:sum(x['wordCount'] for x in baseline[pid]) for pid in people}
    short={pid for pid,n in before.items() if n<TARGET}

    candidates=defaultdict(list); cseen=defaultdict(set)
    if DRAFTS.exists():
        for path in sorted(DRAFTS.rglob('*.json')):
            p=read(path,{})
            for r in rows(p):
                if not isinstance(r,dict) or not source_backed(r): continue
                pid=person_id(r)
                if pid not in short: continue
                for t in texts_from(r):
                    if fp(t) in seen[pid] or fp(t) in cseen[pid]: continue
                    cseen[pid].add(fp(t)); candidates[pid].append({
                        'text':t,'wordCount':wc(t),'kind':'explicit-person-source-extract',
                        'source':{'repositoryPath':str(path.relative_to(ROOT)),'recordId':r.get('id'),'recordTitle':r.get('title'),'source':r.get('source'),'sources':r.get('sources'),'references':r.get('references'),'provenance':r.get('provenance')}
                    })

    if OUT_DIR.exists(): shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True,exist_ok=True)
    index_people={}; residual=[]; extended=0; source_limited=0; added_total=0
    for pid in sorted(short):
        need=max(0,TARGET-before[pid]); kept=[]; added=0
        candidates[pid].sort(key=lambda x:x['wordCount'], reverse=True)
        for x in candidates[pid]:
            kept.append(x); added+=x['wordCount']
            if before[pid]+added>=TARGET: break
        final=before[pid]+added
        status='EXTENDED_TO_500' if final>=TARGET else 'SOURCE_LIMITED'
        if status=='EXTENDED_TO_500': extended+=1
        else:
            source_limited+=1; residual.append({'id':pid,'nameAr':people[pid]['nameAr'],'beforeWords':before[pid],'addedWords':added,'finalWords':final,'missingWords':TARGET-final})
        if kept:
            fn=safe_id(pid)+'.json'; rel=f'data/editorial/short-biography-extensions/{fn}'
            payload={'schema':'short-biography-source-extension-v1','generatedAt':now(),'personId':pid,'personNameAr':people[pid]['nameAr'],
                     'policy':'Explicit-person, source-backed Arabic passages only. No documentary-context padding and no invented factual fill-in.',
                     'targetWords':TARGET,'beforeWords':before[pid],'addedWords':added,'finalWords':final,'status':status,'passages':kept}
            (OUT_DIR/fn).write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            index_people[pid]={'id':pid,'nameAr':people[pid]['nameAr'],'beforeWords':before[pid],'addedWords':added,'finalWords':final,'status':status,'file':rel}
            added_total+=added

    index={'schema':'short-biography-source-extension-index-v1','generatedAt':now(),'targetWords':TARGET,
           'policy':{'directPersonOwnershipOnly':True,'sourceBackedOnly':True,'documentaryContextCountsTowardTarget':False,'inventedFactualFillIn':False},'people':index_people}
    INDEX.write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    audit={'schema':'short-biographies-500-audit-v1','generatedAt':now(),'targetWords':TARGET,'indexedPeople':len(people),
           'below500Before':len(short),'extendedTo500':extended,'sourceLimitedAfter':source_limited,'addedSourceWords':added_total,
           'residualUnder500':residual,'complete':source_limited==0,
           'interpretation':'Only direct, explicitly person-owned, source-backed Arabic text counts. Related documentary context is excluded from the 500-word threshold.'}
    AUDIT.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(audit,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
