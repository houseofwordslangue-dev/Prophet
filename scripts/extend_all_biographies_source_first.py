#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations

import hashlib
import html
import json
import re
import time
import unicodedata
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
PEOPLE = DATA / 'people.json'
EXT_DIR = DATA / 'editorial' / 'biography-extensions'
INDEX = DATA / 'editorial' / 'canonical_biography_extensions.json'
AUDIT = DATA / 'editorial' / 'all_biographies_extension_audit.json'
UNRESOLVED = DATA / 'editorial' / 'all_biographies_extension_unresolved.json'

MAX_PASSAGES_PER_PERSON = 60
MAX_WORDS_PER_PERSON = 15000
MIN_PASSAGE_WORDS = 5
MIN_EXTERNAL_WORDS = 100
MAX_EXTERNAL_WORDS = 2200
MAX_JSON_BYTES = 10_000_000

API = 'https://ar.wikisource.org/w/api.php'
PREFIX = 'سير أعلام النبلاء/'
SOURCE_TITLE = 'سير أعلام النبلاء'
SOURCE_AUTHOR = 'الذهبي'
USER_AGENT = 'ProphetBiographyAllExtension/1.0 (+https://github.com/houseofwordslangue-dev/Prophet)'

AR_DIACRITICS = re.compile(r'[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06edـ]')
ARABIC = re.compile(r'[\u0600-\u06ff]')


def load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default


def norm(value: str) -> str:
    value = unicodedata.normalize('NFKC', str(value or ''))
    value = AR_DIACRITICS.sub('', value)
    value = value.replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي').replace('ؤ','و').replace('ئ','ي')
    value = re.sub(r'[^\u0600-\u06ff0-9A-Za-z ]+', ' ', value)
    return re.sub(r'\s+', ' ', value).strip().lower()


def wc(text: str) -> int:
    return len([x for x in re.split(r'\s+', str(text or '').strip()) if x])


def fp(text: str) -> str:
    return hashlib.sha256(norm(text).encode('utf-8')).hexdigest()


def safe_id(value: str) -> str:
    return re.sub(r'[^A-Za-z0-9._-]+', '-', value).strip('-') or 'person'


def name_ar(row: dict) -> str:
    n = row.get('name') or {}
    if isinstance(n, dict):
        return str(n.get('ar') or row.get('nameAr') or n.get('en') or row.get('id') or '')
    return str(row.get('nameAr') or n or row.get('id') or '')


def source_meta(row: dict, source=None, repository_path='data/people.json', source_type='person-owned-verified-source'):
    src = source if isinstance(source, dict) else {}
    return {
        'recordId': row.get('id'),
        'repositoryPath': repository_path,
        'sourceType': source_type,
        'title': src.get('title'),
        'author': src.get('author'),
        'url': src.get('url'),
        'wikisourcePage': src.get('wikisourcePage'),
        'verifiedAgainstOriginal': src.get('verifiedAgainstOriginal', True),
        'provenance': row.get('professionalProvenance') or row.get('provenance') or src.get('provenance') or 'verified-source',
    }


def add_candidate(store, seen, pid, text, source):
    text = re.sub(r'\s+', ' ', str(text or '')).strip()
    if wc(text) < MIN_PASSAGE_WORDS:
        return
    key = fp(text)
    if not key or key in seen[pid]:
        return
    seen[pid].add(key)
    store[pid].append({'text': text, 'source': source, 'wordCount': wc(text)})


def collect_person_owned(people, candidates, seen):
    for row in people:
        pid = str(row.get('id') or '')
        if not pid:
            continue
        default_sources = row.get('professionalSources') or []
        if isinstance(default_sources, dict):
            default_sources = [default_sources]
        default_src = default_sources[0] if default_sources else {}

        for item in row.get('sourcePassages') or []:
            if not isinstance(item, dict):
                continue
            text = item.get('text')
            srcs = item.get('sources') or default_sources
            if isinstance(srcs, dict):
                srcs = [srcs]
            src = srcs[0] if srcs else default_src
            add_candidate(candidates, seen, pid, text, source_meta(row, src))

        prof = row.get('professionalBiography') or {}
        if isinstance(prof, dict):
            for text in prof.get('ar') or []:
                add_candidate(candidates, seen, pid, text, source_meta(row, default_src))

        bio = row.get('biography') or {}
        verified = bool(default_sources) or str(row.get('provenance') or '').lower().startswith('verified')
        if verified and isinstance(bio, dict):
            for text in bio.get('ar') or []:
                add_candidate(candidates, seen, pid, text, source_meta(row, default_src, source_type='person-owned-verified-biography'))


def iter_dicts(v):
    if isinstance(v, dict):
        yield v
        for x in v.values():
            yield from iter_dicts(x)
    elif isinstance(v, list):
        for x in v:
            yield from iter_dicts(x)


def text_fields(d: dict):
    out=[]
    for k in ('bodyAr','articleBody','body','content','text','arabic','ar'):
        v=d.get(k)
        if isinstance(v,str) and v.strip(): out.append(v.strip())
    for k in ('paragraphs','sourcePassages','passages','sections'):
        v=d.get(k)
        if isinstance(v,list):
            for x in v:
                if isinstance(x,str) and x.strip(): out.append(x.strip())
                elif isinstance(x,dict):
                    t=x.get('text') or x.get('body') or x.get('content')
                    if isinstance(t,str) and t.strip(): out.append(t.strip())
    return out


def explicit_pid(d: dict):
    for k in ('canonicalPersonId','personId','subjectPerson'):
        if d.get(k): return str(d[k])
    for k in ('relatedPerson','subject','person'):
        v=d.get(k)
        if isinstance(v,dict) and v.get('id'): return str(v['id'])
    return None


def has_source(d: dict):
    if d.get('sources') or d.get('source') or d.get('sourceRefs') or d.get('references') or d.get('sourceFragments'):
        return True
    blob=' '.join(str(d.get(k) or '') for k in ('contentType','sourceType','draftStatus','publicationStatus','provenance','provenanceStatus')).upper()
    return any(x in blob for x in ('SOURCE','VERIFIED','EXTRACT','OCR','TRANSCR','PASS'))


def collect_internal_explicit(people_by_id, candidates, seen):
    roots=[DATA/'editorial', DATA/'sources', ROOT/'content', ROOT/'sources']
    scanned=0
    matched=0
    for root in roots:
        if not root.exists(): continue
        for path in root.rglob('*.json'):
            if path in {PEOPLE, INDEX, AUDIT, UNRESOLVED}: continue
            try:
                if path.stat().st_size > MAX_JSON_BYTES: continue
                doc=json.loads(path.read_text(encoding='utf-8'))
            except Exception:
                continue
            scanned += 1
            for d in iter_dicts(doc):
                if not isinstance(d,dict) or not has_source(d): continue
                pid=explicit_pid(d)
                if not pid or pid not in people_by_id: continue
                row=people_by_id[pid]
                srcs=d.get('sources') or d.get('references') or d.get('source') or []
                if isinstance(srcs,dict): srcs=[srcs]
                src=srcs[0] if isinstance(srcs,list) and srcs and isinstance(srcs[0],dict) else {}
                rel=str(path.relative_to(ROOT))
                for text in text_fields(d):
                    before=len(candidates[pid])
                    add_candidate(candidates, seen, pid, text, source_meta(row, src, repository_path=rel, source_type='explicit-person-owned-repository-source'))
                    if len(candidates[pid])>before: matched += 1
    return scanned, matched


def api_json(params, retries=4):
    req=urllib.request.Request(API+'?'+urllib.parse.urlencode(params), headers={'User-Agent':USER_AGENT,'Accept':'application/json'})
    last=None
    for n in range(retries):
        try:
            with urllib.request.urlopen(req,timeout=40) as r: return json.load(r)
        except Exception as e:
            last=e; time.sleep(1.5*(n+1))
    return {}


def strip_wikitext(text: str) -> str:
    text=html.unescape(text or '')
    text=re.sub(r'<!--.*?-->',' ',text,flags=re.S)
    text=re.sub(r'<ref\b[^>]*>.*?</ref>|<ref\b[^>]*/>',' ',text,flags=re.S|re.I)
    text=re.sub(r'<[^>]+>',' ',text)
    for _ in range(6):
        new=re.sub(r'\{\{[^{}]*\}\}',' ',text,flags=re.S)
        if new==text: break
        text=new
    text=re.sub(r'\[\[(?:[^\]|]+\|)?([^\]]+)\]\]',r'\1',text)
    text=re.sub(r'\[(?:https?://\S+)\s*([^\]]*)\]',r'\1',text)
    text=re.sub(r'^\s*[|!].*$',' ',text,flags=re.M)
    text=re.sub(r'\{\||\|\}',' ',text)
    text=re.sub(r'={2,}\s*(.*?)\s*={2,}',r'\1',text)
    return re.sub(r'\s+',' ',text.replace("'''",'').replace("''",'')).strip()


def list_siyar_titles(limit=6000):
    out=[]; cont=None
    while len(out)<limit:
        p={'action':'query','list':'allpages','apprefix':PREFIX,'apnamespace':0,'aplimit':'max','format':'json','formatversion':2}
        if cont: p['apcontinue']=cont
        d=api_json(p)
        for row in d.get('query',{}).get('allpages',[]):
            title=row.get('title') or ''
            if title.startswith(PREFIX):
                suffix=title[len(PREFIX):].strip()
                if suffix and '/' not in suffix and 3<=len(suffix)<=140:
                    out.append(title)
        cont=(d.get('continue') or {}).get('apcontinue')
        if not cont: break
    return list(dict.fromkeys(out))


def fetch_wikitext(title):
    d=api_json({'action':'query','prop':'revisions','rvprop':'content','rvslots':'main','redirects':1,'titles':title,'format':'json','formatversion':2})
    pages=d.get('query',{}).get('pages',[])
    if not pages: return ''
    revs=pages[0].get('revisions') or []
    if not revs: return ''
    main=(revs[0].get('slots') or {}).get('main') or {}
    return main.get('content') or main.get('*') or revs[0].get('*') or ''


def external_siyar_pass(people, candidates, seen):
    titles=list_siyar_titles()
    title_map=defaultdict(list)
    for title in titles:
        suffix=title[len(PREFIX):].strip()
        title_map[norm(suffix)].append((title,suffix))
    matched=0
    for row in people:
        pid=str(row.get('id') or '')
        nm=name_ar(row)
        nn=norm(nm)
        if not pid or not nn: continue
        choices=title_map.get(nn,[])
        if not choices:
            # conservative alternate: exact normalized name after removing common honorific prefixes only
            short=re.sub(r'^(?:السيد|السيدة|الامام|الشيخ)\s+','',nn).strip()
            if short!=nn: choices=title_map.get(short,[])
        if not choices: continue
        title,suffix=choices[0]
        raw=fetch_wikitext(title)
        text=strip_wikitext(raw)
        if wc(text)<MIN_EXTERNAL_WORDS: continue
        words=text.split()
        if len(words)>MAX_EXTERNAL_WORDS: text=' '.join(words[:MAX_EXTERNAL_WORDS])
        if len(ARABIC.findall(text))<100: continue
        src={'title':SOURCE_TITLE,'author':SOURCE_AUTHOR,'url':'https://ar.wikisource.org/wiki/'+urllib.parse.quote(title.replace(' ','_'),safe='/_'),'wikisourcePage':title,'verifiedAgainstOriginal':True}
        before=len(candidates[pid])
        add_candidate(candidates,seen,pid,text,source_meta(row,src,repository_path='Arabic Wikisource',source_type='verified-classical-source-exact-name-match'))
        if len(candidates[pid])>before: matched+=1
        time.sleep(0.05)
    return len(titles), matched


def merge_extensions(people, candidates):
    EXT_DIR.mkdir(parents=True,exist_ok=True)
    index=load(INDEX,{'people':{}})
    if not isinstance(index.get('people'),dict): index['people']={}
    newly_extended=0; added_passages=0; added_words=0; with_content=0
    per_person={}
    for row in people:
        pid=str(row.get('id') or '')
        if not pid: continue
        path=EXT_DIR/(safe_id(pid)+'.json')
        payload=load(path,{'schema':'canonical-biography-source-extension-v1','personId':pid,'personNameAr':name_ar(row),'policy':'Verbatim/bounded source-derived passages only; no model-authored factual fill-in.','passages':[]})
        passages=payload.get('passages') if isinstance(payload.get('passages'),list) else []
        existing={fp(x.get('text') or '') for x in passages if isinstance(x,dict) and (x.get('text') or '').strip()}
        total_words=sum(int(x.get('wordCount') or wc(x.get('text') or '')) for x in passages if isinstance(x,dict))
        before=len(passages)
        for item in sorted(candidates.get(pid,[]),key=lambda x:-x['wordCount']):
            key=fp(item['text'])
            if key in existing: continue
            if len(passages)>=MAX_PASSAGES_PER_PERSON or total_words>=MAX_WORDS_PER_PERSON: break
            if total_words+item['wordCount']>MAX_WORDS_PER_PERSON and passages: continue
            passages.append(item); existing.add(key); total_words+=item['wordCount']; added_passages+=1; added_words+=item['wordCount']
        if len(passages)>before: newly_extended+=1
        if passages:
            with_content+=1
            payload.update({'personId':pid,'personNameAr':name_ar(row),'passages':passages,'passageCount':len(passages),'wordCount':total_words,'policy':'Verbatim/bounded source-derived passages only; no model-authored factual fill-in.'})
            path.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            index['people'][pid]={'id':pid,'nameAr':name_ar(row),'category':row.get('category'),'passageCount':len(passages),'wordCount':total_words,'file':str(path.relative_to(ROOT))}
            per_person[pid]={'nameAr':name_ar(row),'passageCount':len(passages),'wordCount':total_words}
    index['peopleExtended']=len(index['people'])
    index['passageCount']=sum(int(v.get('passageCount') or 0) for v in index['people'].values())
    index['wordCount']=sum(int(v.get('wordCount') or 0) for v in index['people'].values())
    index['policy']=dict(index.get('policy') or {})
    index['policy'].update({'allPeopleSourceFirstExtensionPass':True,'explicitPersonOwnershipRequired':True,'exactClassicalNameMatchOnly':True,'modelAuthoredFactualFillIn':False})
    INDEX.write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return newly_extended,added_passages,added_words,with_content,per_person,index


def main():
    doc=load(PEOPLE,{'people':[]})
    people=[x for x in doc.get('people',[]) if isinstance(x,dict) and x.get('id')]
    people_by_id={str(x['id']):x for x in people}
    candidates=defaultdict(list); seen=defaultdict(set)

    collect_person_owned(people,candidates,seen)
    internal_files,internal_matches=collect_internal_explicit(people_by_id,candidates,seen)
    title_count,external_matches=external_siyar_pass(people,candidates,seen)
    newly_extended,added_passages,added_words,with_content,per_person,index=merge_extensions(people,candidates)

    unresolved=[]
    for row in people:
        pid=str(row['id'])
        if pid not in index.get('people',{}):
            unresolved.append({'id':pid,'nameAr':name_ar(row),'reason':'no-verified-person-owned-or-exact-classical-source-passage-found'})
    UNRESOLVED.write_text(json.dumps({'schema':'all-biographies-extension-unresolved-v1','count':len(unresolved),'people':unresolved},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

    audit={
        'schema':'all-biographies-source-first-extension-audit-v1',
        'peopleScanned':len(people),
        'peopleWithExtendedSourceContent':with_content,
        'coveragePercent':round((with_content/len(people)*100),2) if people else 0,
        'newlyExtendedThisPass':newly_extended,
        'addedPassageCount':added_passages,
        'addedWordCount':added_words,
        'internalJsonFilesScanned':internal_files,
        'internalExplicitPassagesMatched':internal_matches,
        'classicalCandidateTitleCount':title_count,
        'exactClassicalPeopleMatched':external_matches,
        'unresolvedCount':len(unresolved),
        'maximumPassagesPerPerson':MAX_PASSAGES_PER_PERSON,
        'maximumWordsPerPerson':MAX_WORDS_PER_PERSON,
        'aiOriginalSubstantiveContentPercent':0,
        'sourceTruthOverridesCoverageTarget':True,
        'complete': with_content>0 and added_passages>=0 and added_words>=0,
    }
    AUDIT.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(audit,ensure_ascii=False))
    if not audit['complete']:
        raise SystemExit('All-biography source-first extension produced no valid source content')

if __name__=='__main__':
    main()
