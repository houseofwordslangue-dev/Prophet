#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRAFT_ROOT = ROOT / 'data/editorial/drafts'
EXT_DIR = ROOT / 'data/editorial/biography-extensions'
INDEX_PATH = ROOT / 'data/editorial/canonical_biography_extensions.json'
AUDIT_PATH = ROOT / 'data/editorial/global_biography_placement_audit.json'
MAX_PASSAGES_PER_PERSON = 20
MIN_CHARS = 120
MAX_CHARS = 2400
ARABIC = re.compile(r'[\u0600-\u06ff]')
LATIN = re.compile(r'[A-Za-z]')

def read_json(path: Path, default=None):
    try:return json.loads(path.read_text(encoding='utf-8'))
    except Exception:return default

def rows_of(payload):
    if isinstance(payload,list):return payload
    if isinstance(payload,dict):
        for key in ('drafts','items','articles','records'):
            if isinstance(payload.get(key),list):return payload[key]
    return []

def explicit_person(row: dict):
    for key in ('relatedPerson','subject'):
        obj=row.get(key)
        if isinstance(obj,dict) and obj.get('id'):
            return str(obj['id']),str(obj.get('name') or obj.get('nameAr') or row.get('canonicalPersonName') or obj['id'])
    for key in ('canonicalPersonId','subjectPerson','personId'):
        if row.get(key):return str(row[key]),str(row.get('canonicalPersonName') or row.get('nameAr') or row[key])
    return None

def source_backed(row: dict)->bool:
    markers=' '.join(str(row.get(k) or '') for k in ('contentType','draftStatus','publicationStatus','sourceType')).upper()
    if any(x in markers for x in ('SOURCE','VERIFIED','EXTRACT','TRANSCR','OCR')):return True
    return bool(row.get('sources') or row.get('sourceRefs') or row.get('references') or row.get('provenance') or row.get('source'))

def life_intent(row: dict)->bool:
    markers=' '.join(str(row.get(k) or '') for k in ('articleKind','editorialCategory','contentType','publicRole')).lower()
    if any(x in markers for x in ('biography','life-biograph','life-profile','canonical-biography-chapter')):return True
    if row.get('biographyPlacement') is True:return True
    title=row.get('title') or ''
    if isinstance(title,dict):title=' '.join(str(v) for v in title.values())
    return bool(re.search(r'سيرت(?:ه|ها)?\s*وحيات(?:ه|ها)?|(?:^|\s)سيرة\s+|\bbiograph(?:y|ies)\b|\bvie\s+de\b',str(title),re.I))

def texts_of(row: dict):
    seen=set()
    for key in ('paragraphs','sourcePassages','passages'):
        seq=row.get(key)
        if not isinstance(seq,list):continue
        for item in seq:
            text=item.get('text') if isinstance(item,dict) else item
            text=re.sub(r'\s+',' ',str(text or '')).strip()
            if text and text not in seen:seen.add(text);yield text
    for key in ('body','content','text','articleBody','bodyAr'):
        value=row.get(key)
        if isinstance(value,str):
            text=re.sub(r'\s+',' ',value).strip()
            if text and text not in seen:seen.add(text);yield text

def acceptable(text: str):
    if len(text)<MIN_CHARS:return None
    ar=len(ARABIC.findall(text));lat=len(LATIN.findall(text))
    if ar<80 or lat>max(20,ar//5):return None
    return text[:MAX_CHARS].rstrip() if len(text)>MAX_CHARS else text

def fp(text: str)->str:return hashlib.sha256(re.sub(r'\s+',' ',text).encode('utf-8')).hexdigest()

def source_meta(row: dict,rel: str):
    sources=row.get('sources') or row.get('references') or []
    if isinstance(sources,dict):sources=[sources]
    meta={'repositoryPath':rel,'recordId':row.get('id'),'recordTitle':row.get('title'),'sourceType':'explicit-person-owned-editorial-extraction'}
    if isinstance(sources,list) and sources:meta['sources']=sources[:8]
    if row.get('sourceRefs'):meta['sourceRefs']=row.get('sourceRefs')[:40] if isinstance(row.get('sourceRefs'),list) else row.get('sourceRefs')
    if row.get('provenance'):meta['provenance']=row.get('provenance')
    if row.get('source'):meta['source']=row.get('source')
    return meta

def safe_id(value: str)->str:return re.sub(r'[^A-Za-z0-9._-]+','-',value).strip('-') or 'person'

def main():
    prior_index=read_json(INDEX_PATH,{}) or {}; candidates=defaultdict(list);person_names={};person_categories={pid:meta.get('category') for pid,meta in (prior_index.get('people') or {}).items()};seen=defaultdict(set);source_records_scanned=explicit_source_records=0
    for path in sorted(DRAFT_ROOT.glob('**/*.json')):
        payload=read_json(path,{});rel=str(path.relative_to(ROOT))
        for row in rows_of(payload):
            if not isinstance(row,dict):continue
            source_records_scanned+=1;person=explicit_person(row)
            if not person or not source_backed(row):continue
            explicit_source_records+=1;pid,name=person;person_names.setdefault(pid,name);priority=0 if life_intent(row) else 1;meta=source_meta(row,rel)
            for raw in texts_of(row):
                text=acceptable(raw)
                if not text:continue
                key=fp(text)
                if key in seen[pid]:continue
                seen[pid].add(key);candidates[pid].append({'text':text,'wordCount':len(text.split()),'source':meta,'_priority':priority})
    EXT_DIR.mkdir(parents=True,exist_ok=True)
    for stale in EXT_DIR.glob('*.json'):stale.unlink()
    people={};total_passages=total_words=capped_away=0
    for pid,rows in sorted(candidates.items()):
        rows.sort(key=lambda x:(x['_priority'],-len(x['text'])));capped_away+=max(0,len(rows)-MAX_PASSAGES_PER_PERSON);kept=rows[:MAX_PASSAGES_PER_PERSON]
        if not kept:continue
        for item in kept:item.pop('_priority',None)
        fname=safe_id(pid)+'.json';relfile=f'data/editorial/biography-extensions/{fname}'
        payload={'schema':'canonical-biography-source-extension-v2','personId':pid,'personNameAr':person_names.get(pid,pid),'policy':'Only source passages from records explicitly linked to this exact person; no name-only or cross-person enrichment.','passageCount':len(kept),'passages':kept}
        (EXT_DIR/fname).write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        words=sum(x['wordCount'] for x in kept);total_passages+=len(kept);total_words+=words;people[pid]={'id':pid,'nameAr':person_names.get(pid,pid),'category':person_categories.get(pid),'passageCount':len(kept),'wordCount':words,'file':relfile}
    index={'schema':'canonical-biography-source-extension-index-v2','policy':{'onePersonOneCanonicalBiographyPage':True,'extensionsRenderOnlyOnCanonicalPersonPage':True,'sourceDerivedOnly':True,'explicitPersonOwnershipRequiredBeforeCap':True,'incidentalNameMatchesRejected':True,'crossPersonRecordsRejected':True,'noGeneratedFactualFillIn':True,'thematicArticlesRemainInSections':True},'indexedPeople':prior_index.get('indexedPeople',379),'peopleExtended':len(people),'passageCount':total_passages,'wordCount':total_words,'people':people}
    INDEX_PATH.write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    audit=read_json(AUDIT_PATH,{}) or {};audit.update({'biographyExtensionOwnershipPolicy':'explicit-person-link-before-ranking-and-cap','sourceRecordsScannedForStrictExtensions':source_records_scanned,'explicitPersonOwnedSourceRecords':explicit_source_records,'peopleExtendedAfterStrictRebuild':len(people),'extensionPassagesAfterStrictRebuild':total_passages,'extensionWordsAfterStrictRebuild':total_words,'candidatePassagesCappedAfterOwnershipCheck':capped_away,'strictExtensionOwnershipComplete':True});AUDIT_PATH.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'peopleExtended':len(people),'passages':total_passages,'words':total_words,'explicitSourceRecords':explicit_source_records,'cappedAfterOwnership':capped_away,'aliPresent':'ali-ibn-abi-talib' in people,'fatimaPresent':'fatima-al-zahra' in people,'khadijaPresent':'khadija-bint-khuwaylid' in people},ensure_ascii=False))
    if not people or not total_passages:raise SystemExit('Strict biography rebuild produced no source extensions')
if __name__=='__main__':main()
