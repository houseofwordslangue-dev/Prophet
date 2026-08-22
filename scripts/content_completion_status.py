#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REG=ROOT/'data/editorial_sections.json'
EDITORIAL=ROOT/'data/editorial'
STATE=EDITORIAL/'content_completion_state.json'
SLOT_AUDIT=EDITORIAL/'content_completion_slot_audit.json'
BIO_AUDIT=EDITORIAL/'required_biographies_audit.json'
TARGET=50
QUALIFY_STATUSES={'PUBLISHED','PUBLIC','READY','DRAFT_SOURCE_VERIFIED','SOURCE_VERIFIED'}
SKIP_NAMES={'content_completion_state.json','content_completion_slot_audit.json','required_biographies_audit.json','empty_biographies_audit.json'}

def load(p,default):
    try:return json.loads(p.read_text(encoding='utf-8'))
    except Exception:return default

def source_refs(o):
    if not isinstance(o,dict):return []
    out=[]
    for k in ('sources','sourceRefs','references','resourceRefs','sourceIds','resourceIds'):
        v=o.get(k)
        if isinstance(v,list):out.extend(v)
        elif v:out.append(v)
    for p in o.get('paragraphs') or []:
        if isinstance(p,dict):out.extend(p.get('sourceRefs') or [])
    return [x for x in out if x]

def has_content(o):
    if not isinstance(o,dict):return False
    if any(str(o.get(k) or '').strip() for k in ('body','content','text','articleBody')):return True
    ps=o.get('paragraphs') or []
    return any(isinstance(p,dict) and str(p.get('text') or '').strip() for p in ps)

def qualifies(o):
    if not isinstance(o,dict) or not o.get('id') or not o.get('section') or not o.get('subsection'):return False
    status=str(o.get('publicationStatus') or o.get('status') or o.get('draftStatus') or '').upper()
    if status not in QUALIFY_STATUSES:return False
    if not has_content(o):return False
    grounded=(o.get('sourceCoveragePercent')==100) or bool(source_refs(o))
    if o.get('aiOriginalSubstantiveContentPercent') not in (None,0):return False
    return grounded

def walk(v):
    if isinstance(v,dict):
        yield v
        for x in v.values():yield from walk(x)
    elif isinstance(v,list):
        for x in v:yield from walk(x)

def main():
    reg=load(REG,{})
    slots=[x for x in reg.get('sections',[]) if x.get('active') and x.get('editorial')]
    slot_ids=[str(x.get('id') or f"{x.get('section')}/{x.get('subsection')}") for x in slots]
    counts={s:0 for s in slot_ids}; seen=set()
    for p in EDITORIAL.rglob('*.json'):
        if p.name in SKIP_NAMES:continue
        try:doc=json.loads(p.read_text(encoding='utf-8'))
        except Exception:continue
        for o in walk(doc):
            if not qualifies(o):continue
            aid=str(o.get('id')); key=f"{o.get('section')}/{o.get('subsection')}"
            if key not in counts or aid in seen:continue
            seen.add(aid);counts[key]+=1
    under=[{'slot':s,'count':counts[s],'deficit':max(0,TARGET-counts[s])} for s in slot_ids if counts[s]<TARGET]
    under.sort(key=lambda x:(x['count'],x['slot']))
    empty=[x['slot'] for x in under if x['count']==0]

    audit=load(SLOT_AUDIT,{}); now=datetime.now(timezone.utc); recent_cutoff=now-timedelta(hours=12)
    def recently_blocked(slot):
        row=(audit.get('slots') or {}).get(slot) or {}
        if row.get('status') not in {'NEEDS_SOURCE','RETRYABLE'}:return False
        try:return datetime.fromisoformat(str(row.get('at')).replace('Z','+00:00'))>=recent_cutoff
        except Exception:return False
    eligible=[x for x in under if not recently_blocked(x['slot'])]
    next_slot=(eligible or under)[0]['slot'] if under else None

    bio=load(BIO_AUDIT,{})
    missing=bio.get('missing') or []
    missing_ids=[str(x.get('id')) for x in missing if isinstance(x,dict) and x.get('id')]
    article_complete=not under
    bio_complete=(bio.get('missingCanonicalBiographyCount')==0) if bio else False
    state={
      'schema':'content-completion-state-v1','generatedAt':now.isoformat(),
      'activeEditorialSlotCount':len(slot_ids),'targetArticlesPerSlot':TARGET,
      'articleCountsBySlot':counts,'underTargetSlots':under,'emptySlots':empty,
      'nextTargetSlot':next_slot,'ARTICLE_FILL_COMPLETE':article_complete,
      'biographyRequiredPersonCount':bio.get('requiredPersonCount'),
      'missingCanonicalBiographyCount':bio.get('missingCanonicalBiographyCount'),
      'missingBiographyIds':missing_ids,'BIOGRAPHY_FILL_COMPLETE':bio_complete,
      'COMPLETION_PROMPT_COMPLETE':bool(article_complete and bio_complete),
      'governedBy':'MASTER-OVERRIDING-SITE-INSTRUCTION.md'
    }
    STATE.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(state,ensure_ascii=False))
    return 0
if __name__=='__main__':raise SystemExit(main())
