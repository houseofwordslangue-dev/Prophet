#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations
import json,re,unicodedata,urllib.parse,urllib.request,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'
PEOPLE=DATA/'people.json'
FAMILY=DATA/'family_people.json'
QUAR=DATA/'editorial'/'non_person_people_registry_quarantine.json'
AUDIT=DATA/'editorial'/'biography_gap_repair_audit.json'

ROLE_SUFFIX=re.compile(r'\s*\((?:translator|editor|compiler|commentator)\)\s*$',re.I)
RESOURCE_PATTERNS=[
    re.compile(r'\btradition(?:s)?\b',re.I),
    re.compile(r'\brelevant discussions?\b',re.I),
    re.compile(r'\bespecially passages?\b',re.I),
    re.compile(r'\buse with source-critical notes\b',re.I),
    re.compile(r'\bhadith compilations?\b',re.I),
]
KNOWN_AR={
 'Ahmad ibn al-Mubarak al-Lamati':'أحمد بن المبارك اللمطي',
 'Ibn Abi ʿAsim':'ابن أبي عاصم',
 'Ibn Hibban':'ابن حبان',
 'Ibn al-Dibaʿ':'ابن الديبع',
 'Ibn al-Qattan al-Fasi':'ابن القطان الفاسي',
 'Imam Malik':'مالك بن أنس',
 'Muhammad al-Sibaʿi al-Marrakushi':'محمد السباعي المراكشي',
 'Muhammad ibn Qasim Jassus al-Fasi':'محمد بن قاسم جسوس الفاسي',
 'Omar Khayyam':'عمر الخيام',
 'Rumi':'جلال الدين الرومي',
 'al-Baladhuri':'البلاذري',
 'al-Darimi':'الدارمي',
}

def load(p,d):
    try:return json.loads(p.read_text(encoding='utf-8'))
    except Exception:return d

def latin_only(s):
    s=str(s or '')
    return bool(re.search(r'[A-Za-z]',s)) and not bool(re.search(r'[\u0600-\u06ff]',s))

def norm(s):
    s=unicodedata.normalize('NFKC',str(s or ''))
    s=re.sub(r'[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06edـ]','',s)
    s=s.replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي')
    return re.sub(r'[^\u0600-\u06ffA-Za-z0-9]+',' ',s).strip().lower()

def slugish(s):
    s=str(s or '')
    return bool(re.fullmatch(r'[A-Za-z0-9]+(?:-[A-Za-z0-9]+){1,}',s))

def family_index():
    doc=load(FAMILY,{'people':[]})
    out={}
    for r in doc.get('people',[]):
        if not isinstance(r,dict):continue
        for k in (r.get('id'),r.get('slug')):
            if k: out[str(k).lower()]=r
    return out

def merge_family(row,src):
    n=row.get('name') if isinstance(row.get('name'),dict) else {}
    sn=src.get('name') if isinstance(src.get('name'),dict) else {}
    row['name']={
      'ar':sn.get('ar') or n.get('ar') or row.get('nameAr') or row.get('id'),
      'en':n.get('en') or sn.get('en') or n.get('ar') or row.get('id'),
      'fr':n.get('fr') or sn.get('fr') or n.get('en') or sn.get('en') or row.get('id')
    }
    if src.get('sourcePassages'):
        existing=row.get('sourcePassages') if isinstance(row.get('sourcePassages'),list) else []
        texts={norm((x or {}).get('text')) for x in existing if isinstance(x,dict)}
        for p in src.get('sourcePassages') or []:
            if isinstance(p,dict) and norm(p.get('text')) not in texts:
                existing.append(p);texts.add(norm(p.get('text')))
        row['sourcePassages']=existing
    if src.get('provenance') and str(src.get('provenance')).startswith('verified'):
        row['provenance']='verified-source-excerpt'
    row['canonicalFamilySourceId']=src.get('id')
    return row

def clean_person_label(row):
    n=row.get('name') if isinstance(row.get('name'),dict) else {}
    ar=str(n.get('ar') or row.get('nameAr') or '')
    original=ar
    ar=ROLE_SUFFIX.sub('',ar).strip()
    ar=re.sub(r',\s*relevant discussions.*$','',ar,flags=re.I)
    ar=re.sub(r',\s*especially passages.*$','',ar,flags=re.I)
    ar=re.sub(r';\s*use with source-critical notes.*$','',ar,flags=re.I)
    if ar in KNOWN_AR:
        n['en']=n.get('en') or ar
        ar=KNOWN_AR[ar]
    if ar!=original:
        n['ar']=ar
        row['name']=n
        row.setdefault('registryRepairs',[]).append({'type':'canonical-name-cleanup','from':original,'to':ar})
        return True
    return False

def wikidata_ar_label(name):
    if not name or not latin_only(name): return None
    base=ROLE_SUFFIX.sub('',name).strip()
    params=urllib.parse.urlencode({'action':'wbsearchentities','search':base,'language':'en','format':'json','limit':5,'type':'item','origin':'*'})
    req=urllib.request.Request('https://www.wikidata.org/w/api.php?'+params,headers={'User-Agent':'ProphetBiographyGapRepair/1.0'})
    try:
        with urllib.request.urlopen(req,timeout=20) as r: d=json.load(r)
    except Exception:return None
    target=norm(base)
    qid=None
    for x in d.get('search',[]):
        labels=[x.get('label')]+(x.get('aliases') or [])
        if any(norm(v)==target for v in labels if v):
            qid=x.get('id');break
    if not qid:return None
    params=urllib.parse.urlencode({'action':'wbgetentities','ids':qid,'props':'labels','languages':'ar|en','format':'json','origin':'*'})
    req=urllib.request.Request('https://www.wikidata.org/w/api.php?'+params,headers={'User-Agent':'ProphetBiographyGapRepair/1.0'})
    try:
        with urllib.request.urlopen(req,timeout=20) as r: d=json.load(r)
        ent=(d.get('entities') or {}).get(qid) or {}
        ar=((ent.get('labels') or {}).get('ar') or {}).get('value')
        return ar if ar and re.search(r'[\u0600-\u06ff]',ar) else None
    except Exception:return None

def main():
    doc=load(PEOPLE,{'people':[]})
    people=[x for x in doc.get('people',[]) if isinstance(x,dict)]
    fam=family_index()
    kept=[]; quarantined=[]
    family_merged=0; cleaned=0; wikidata_added=0
    for row in people:
        n=row.get('name') if isinstance(row.get('name'),dict) else {}
        ar=str(n.get('ar') or row.get('nameAr') or '')
        # Quarantine only obvious non-person/resource labels; preserve every ambiguous case.
        if ';' in ar or any(p.search(ar) for p in RESOURCE_PATTERNS):
            row['quarantineReason']='resource-or-compound-attribution-not-a-single-person'
            quarantined.append(row);continue
        key=None
        if slugish(ar): key=ar.lower()
        elif row.get('slug') and str(row.get('slug')).lower() in fam: key=str(row.get('slug')).lower()
        if key and key in fam:
            row=merge_family(row,fam[key]);family_merged+=1
        if clean_person_label(row): cleaned+=1
        n=row.get('name') if isinstance(row.get('name'),dict) else {}
        ar=str(n.get('ar') or row.get('nameAr') or '')
        if latin_only(ar):
            resolved=wikidata_ar_label(ar)
            if resolved:
                n['en']=n.get('en') or ar
                n['ar']=resolved
                row['name']=n
                row.setdefault('registryRepairs',[]).append({'type':'wikidata-ar-label','from':ar,'to':resolved})
                wikidata_added+=1
                time.sleep(0.03)
        kept.append(row)
    doc['people']=kept;doc['count']=len(kept)
    PEOPLE.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    QUAR.write_text(json.dumps({'schema':'non-person-people-registry-quarantine-v1','count':len(quarantined),'people':quarantined},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    audit={
      'schema':'biography-gap-repair-audit-v1','beforeCount':len(people),'afterValidPersonCount':len(kept),
      'quarantinedNonPersonOrCompoundCount':len(quarantined),'familyCanonicalRecordsMerged':family_merged,
      'canonicalLabelsCleaned':cleaned,'wikidataArabicLabelsAdded':wikidata_added,
      'remainingLatinOnlyNameCount':sum(1 for r in kept if latin_only(((r.get('name') or {}).get('ar') if isinstance(r.get('name'),dict) else r.get('nameAr')))),
      'complete':True
    }
    AUDIT.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(audit,ensure_ascii=False))
if __name__=='__main__':main()
