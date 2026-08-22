#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations

import json, re, shutil, hashlib
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'; EDIT=DATA/'editorial'; DRAFTS=EDIT/'drafts'
OUT_DIR=EDIT/'short-biography-extensions'; INDEX=EDIT/'short_biography_extensions.json'; AUDIT=EDIT/'short_biographies_500_audit.json'
TARGET=500
AR=re.compile(r'[\u0600-\u06ff]'); DIAC=re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06EDـ]')
BIO_KEYS=('biographyAr','biography','bio','bodyAr','summaryAr','descriptionAr','contentAr','textAr','articleBody','body','content','text','paragraphs','sourcePassages','passages','chapters')

def now(): return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def read(p,default=None):
    try:return json.loads(p.read_text(encoding='utf-8'))
    except Exception:return default

def norm(s):
    s=DIAC.sub('',str(s or '')).replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي')
    s=re.sub(r'[^\u0600-\u06ffA-Za-z0-9\s-]',' ',s)
    return re.sub(r'\s+',' ',s).strip().lower()
def wc(s): return len(re.findall(r'\S+',re.sub(r'\s+',' ',str(s or '')).strip()))
def fp(s): return hashlib.sha256(norm(s).encode()).hexdigest()
def safe_id(s): return re.sub(r'[^A-Za-z0-9._-]+','-',str(s)).strip('-') or 'person'
def arabic_ratio(s):
    s=str(s or ''); letters=len(re.findall(r'[A-Za-z\u0600-\u06ff]',s)); return len(AR.findall(s))/max(1,letters)
def readable_arabic(s):
    s=re.sub(r'\s+',' ',str(s or '')).strip(); toks=s.split()
    if len(toks)<12 or arabic_ratio(s)<.72:return False
    lens=[len(DIAC.sub('',t)) for t in toks]
    too_long=sum(1 for n in lens if n>20)
    if max(lens,default=0)>45 or too_long/max(1,len(lens))>.04:return False
    if sum(1 for t in toks if re.search(r'[|<>_=]{2,}',t))/max(1,len(toks))>.02:return False
    return True

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

def strings_from(obj, depth=0):
    if depth>6:return []
    out=[]
    if isinstance(obj,str):
        s=re.sub(r'\s+',' ',obj).strip()
        if readable_arabic(s):out.append(s)
    elif isinstance(obj,list):
        for x in obj:out.extend(strings_from(x,depth+1))
    elif isinstance(obj,dict):
        for k in BIO_KEYS:
            if k in obj:out.extend(strings_from(obj[k],depth+1))
    return out

def collect_people():
    people={}; aliases=defaultdict(set)
    for path,key in [(DATA/'people.json','people'),(DATA/'family_people.json','people'),(DATA/'family_groups.json','registry'),(DATA/'family_biographies.json','people'),(DATA/'expanded_people_135.json','people')]:
        p=read(path,{}) or {}; seq=p.get(key,[]) if isinstance(p,dict) else []
        for r in seq:
            if not isinstance(r,dict) or not r.get('id'):continue
            pid=str(r['id']); n=r.get('nameAr')
            if not n:
                nm=r.get('name')
                n=nm.get('ar') if isinstance(nm,dict) else nm if isinstance(nm,str) else None
            if not n:continue
            people.setdefault(pid,{'id':pid,'nameAr':str(n),'category':r.get('category') or ''})
            nn=norm(n)
            if len(AR.findall(nn))>=3:aliases[pid].add(nn)
    return people,aliases

def add(bucket,seen,pid,text,source,kind):
    if not readable_arabic(text):return
    k=fp(text)
    if k in seen[pid]:return
    seen[pid].add(k);bucket[pid].append({'text':text,'wordCount':wc(text),'source':source,'kind':kind})

def source_meta(r,path):
    return {'repositoryPath':str(path.relative_to(ROOT)),'recordId':r.get('id'),'recordTitle':r.get('title'),
            'source':r.get('source'),'sources':r.get('sources'),'references':r.get('references'),'provenance':r.get('provenance')}

def title_matches_person(title,names):
    h=norm(title)
    return any(n and len(n)>=5 and n in h for n in names)

def direct_windows(text,names,title_owned=False):
    text=re.sub(r'\s+',' ',str(text or '')).strip()
    if not readable_arabic(text):return []
    nt=norm(text)
    if title_owned:
        # A source-backed record explicitly titled for the person is treated as person-owned,
        # but cap very large records to avoid pulling adjacent unrelated material wholesale.
        toks=text.split()
        return [' '.join(toks[:1200])] if len(toks)>1200 else [text]
    hits=[n for n in names if n and n in nt]
    if not hits:return []
    # For unowned text, keep bounded sentence context around an exact distinctive name only.
    parts=[x.strip() for x in re.split(r'(?<=[.!؟؛])\s+|\n+',text) if x.strip()]
    out=[]
    for i,p in enumerate(parts):
        np=norm(p)
        if not any(n in np for n in hits):continue
        chunk=' '.join(parts[max(0,i-1):min(len(parts),i+4)])
        if readable_arabic(chunk):out.append(chunk)
    return out

def main():
    people,aliases=collect_people();baseline=defaultdict(list);seen=defaultdict(set)

    # Exact-id canonical Arabic biographies.
    canonical_files=[DATA/'people.json',DATA/'family_people.json',DATA/'family_groups.json',DATA/'family_biographies.json',DATA/'expanded_biographies_135_full.json',EDIT/'canonical_biographies.json',EDIT/'biography_repairs_20260821.json']
    for path in canonical_files:
        p=read(path,{})
        for r in rows(p):
            if not isinstance(r,dict):continue
            pid=str(r.get('id') or r.get('personId') or r.get('canonicalPersonId') or '')
            if pid not in people:continue
            for t in strings_from(r):add(baseline,seen,pid,t,{'repositoryPath':str(path.relative_to(ROOT))},'canonical-direct')

    # Canonical life chapters: count only bounded clauses/windows that explicitly name the target.
    life=EDIT/'canonical-life'
    if life.exists():
        for path in life.glob('*.json'):
            p=read(path,{}) or {};pid=str(p.get('personId') or '')
            if pid not in people:continue
            names=aliases[pid]
            for ch in p.get('chapters',[]) if isinstance(p.get('chapters'),list) else []:
                body=str(ch.get('body') or '')
                for t in direct_windows(body,names,False):add(baseline,seen,pid,t,{'repositoryPath':str(path.relative_to(ROOT)),'recordId':ch.get('id'),'sources':ch.get('sources')},'canonical-life-direct-window')

    # Existing v2 strict extensions: accept only readable exact-person passages; corrupted OCR is excluded.
    ext=EDIT/'biography-extensions'
    rejected_ocr=0
    if ext.exists():
        for path in ext.glob('*.json'):
            p=read(path,{}) or {};pid=str(p.get('personId') or '')
            if pid not in people:continue
            for x in p.get('passages',[]) if isinstance(p.get('passages'),list) else []:
                t=str(x.get('text') or '')
                if not readable_arabic(t):rejected_ocr+=1;continue
                add(baseline,seen,pid,t,x.get('source') or {'repositoryPath':str(path.relative_to(ROOT))},'existing-readable-strict-extension')

    before={pid:sum(x['wordCount'] for x in baseline[pid]) for pid in people};short={pid for pid,n in before.items() if n<TARGET}
    candidates=defaultdict(list);cseen=defaultdict(set)

    # Mine every source-backed editorial record. Explicit person id wins; otherwise require the exact
    # Arabic person name in the source-record title. Generic incidental body-name hits are not enough.
    if DRAFTS.exists():
        for path in sorted(DRAFTS.rglob('*.json')):
            p=read(path,{})
            for r in rows(p):
                if not isinstance(r,dict) or not source_backed(r):continue
                explicit=person_id(r); title=str(r.get('title') or '')
                target_ids=[]
                if explicit in short:target_ids=[explicit]
                elif explicit is None:
                    for pid in short:
                        if aliases[pid] and title_matches_person(title,aliases[pid]):target_ids.append(pid)
                if not target_ids:continue
                raw=[]
                for k in BIO_KEYS:
                    if k in r:
                        v=r[k]
                        if isinstance(v,str):raw.append(v)
                        elif isinstance(v,list):
                            for x in v:
                                if isinstance(x,str):raw.append(x)
                                elif isinstance(x,dict):raw.append(str(x.get('text') or x.get('body') or x.get('content') or ''))
                for pid in target_ids:
                    owned=(explicit==pid) or title_matches_person(title,aliases[pid])
                    for txt in raw:
                        for t in direct_windows(txt,aliases[pid],owned):
                            k=fp(t)
                            if k in seen[pid] or k in cseen[pid]:continue
                            cseen[pid].add(k);candidates[pid].append({'text':t,'wordCount':wc(t),'kind':'source-owned-direct-extract','source':source_meta(r,path)})

    if OUT_DIR.exists():shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True,exist_ok=True)
    index_people={};residual=[];extended=0;source_limited=0;added_total=0
    for pid in sorted(short):
        kept=[];added=0
        candidates[pid].sort(key=lambda x:x['wordCount'],reverse=True)
        for x in candidates[pid]:
            kept.append(x);added+=x['wordCount']
            if before[pid]+added>=TARGET:break
        final=before[pid]+added;status='EXTENDED_TO_500' if final>=TARGET else 'SOURCE_LIMITED'
        if status=='EXTENDED_TO_500':extended+=1
        else:
            source_limited+=1;residual.append({'id':pid,'nameAr':people[pid]['nameAr'],'beforeWords':before[pid],'addedWords':added,'finalWords':final,'missingWords':TARGET-final})
        if kept:
            fn=safe_id(pid)+'.json';rel=f'data/editorial/short-biography-extensions/{fn}'
            payload={'schema':'short-biography-source-extension-v2','generatedAt':now(),'personId':pid,'personNameAr':people[pid]['nameAr'],'targetWords':TARGET,
                     'policy':'Readable, direct, person-owned, source-backed Arabic only; no documentary-context padding and no invented factual fill-in.',
                     'beforeWords':before[pid],'addedWords':added,'finalWords':final,'status':status,'passages':kept}
            (OUT_DIR/fn).write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            index_people[pid]={'id':pid,'nameAr':people[pid]['nameAr'],'beforeWords':before[pid],'addedWords':added,'finalWords':final,'status':status,'file':rel};added_total+=added

    INDEX.write_text(json.dumps({'schema':'short-biography-source-extension-index-v2','generatedAt':now(),'targetWords':TARGET,
        'policy':{'directPersonOwnershipOnly':True,'sourceBackedOnly':True,'readableArabicOnly':True,'collapsedOcrRejected':True,'documentaryContextCountsTowardTarget':False,'inventedFactualFillIn':False},'people':index_people},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    audit={'schema':'short-biographies-500-audit-v2','generatedAt':now(),'targetWords':TARGET,'indexedPeople':len(people),'below500Before':len(short),
           'extendedTo500':extended,'sourceLimitedAfter':source_limited,'addedSourceWords':added_total,'rejectedUnreadableExistingOcrPassages':rejected_ocr,
           'residualUnder500':residual,'complete':source_limited==0,
           'interpretation':'Only readable direct person-owned source-backed Arabic counts. Collapsed OCR and related documentary context are excluded.'}
    AUDIT.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(audit,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
