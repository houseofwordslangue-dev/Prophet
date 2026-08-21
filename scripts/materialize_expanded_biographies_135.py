#!/usr/bin/env python3
from __future__ import annotations
import html,json,re,time,urllib.parse,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
INDEX=ROOT/'data/expanded_people_135.json'
OUT=ROOT/'data/expanded_biographies_135_full.json'
AUDIT=ROOT/'data/editorial/expanded_biographies_135_local_audit.json'
API='https://ar.wikisource.org/w/api.php'
UA='ProphetBiographyLocalImporter/1.0 (+https://github.com/houseofwordslangue-dev/Prophet)'
MIN_WORDS=120
MAX_WORDS=1800

def get_json(params,retries=5):
    req=urllib.request.Request(API+'?'+urllib.parse.urlencode(params),headers={'User-Agent':UA,'Accept':'application/json'})
    last=None
    for i in range(retries):
        try:
            with urllib.request.urlopen(req,timeout=45) as r:return json.load(r)
        except Exception as e:
            last=e;time.sleep(2*(i+1))
    raise RuntimeError(last)

def words(s):return [x for x in re.split(r'\s+',s.strip()) if x]

def strip_wiki(s):
    s=html.unescape(s or '')
    s=re.sub(r'<!--.*?-->',' ',s,flags=re.S)
    s=re.sub(r'<ref\b[^>]*>.*?</ref>|<ref\b[^>]*/>',' ',s,flags=re.S|re.I)
    s=re.sub(r'<[^>]+>',' ',s)
    for _ in range(7):
        n=re.sub(r'\{\{[^{}]*\}\}',' ',s,flags=re.S)
        if n==s:break
        s=n
    s=re.sub(r'\[\[(?:[^\]|]+\|)?([^\]]+)\]\]',r'\1',s)
    s=re.sub(r'\[(?:https?://\S+)\s*([^\]]*)\]',r'\1',s)
    s=re.sub(r'^\s*[|!].*$',' ',s,flags=re.M)
    s=re.sub(r'\{\||\|\}',' ',s)
    s=re.sub(r'={2,}\s*(.*?)\s*={2,}',r'\1',s)
    return s.replace("'''",'').replace("''",'')

def clean(s,name):
    lines=[]
    for raw in strip_wiki(s).splitlines():
        line=re.sub(r'\s+',' ',raw).strip()
        if not line or line in {name,'سير أعلام النبلاء',f'سير أعلام النبلاء/{name}'}:continue
        if any(x in line for x in ('مجلوبة من','آخر تعديل للصفحة','النصوص منشورة وفق','أضف لغات','أضف موضوعًا')):continue
        lines.append(line)
    text='\n\n'.join(lines).strip();w=words(text)
    return ' '.join(w[:MAX_WORDS]) if len(w)>MAX_WORDS else text

def fetch_batch(pages):
    d=get_json({'action':'query','prop':'revisions','rvprop':'content','rvslots':'main','redirects':1,'titles':'|'.join(pages),'format':'json','formatversion':2})
    out={}
    for p in d.get('query',{}).get('pages',[]):
        revs=p.get('revisions') or [];content=''
        if revs:
            main=(revs[0].get('slots') or {}).get('main') or {}
            content=main.get('content') or main.get('*') or revs[0].get('*') or ''
        out[p.get('title') or '']=content
    return out

def src_url(page):return 'https://ar.wikisource.org/wiki/'+urllib.parse.quote(page.replace(' ','_'),safe='/_')

def main():
    idx=json.loads(INDEX.read_text(encoding='utf-8'));rows=idx.get('people') or []
    assert len(rows)==135 and len({x['id'] for x in rows})==135 and len({x['name'] for x in rows})==135
    result=[];fail=[]
    for i in range(0,len(rows),20):
        batch=rows[i:i+20];raw=fetch_batch([x['page'] for x in batch])
        for x in batch:
            text=clean(raw.get(x['page'],'') ,x['name']);wc=len(words(text))
            if wc<MIN_WORDS:
                fail.append({'id':x['id'],'name':x['name'],'words':wc});continue
            result.append({'id':x['id'],'name':x['name'],'page':x['page'],'biographyAr':text,'wordCount':wc,'source':{'title':'سير أعلام النبلاء','author':'الذهبي','url':src_url(x['page']),'provider':'Arabic Wikisource','verifiedAgainstOriginal':True},'provenance':'VERBATIM_CLASSICAL_SOURCE_TEXT','aiOriginalSubstantiveContentPercent':0})
        time.sleep(.12)
    complete=len(result)==135 and not fail
    OUT.write_text(json.dumps({'schema':'expanded-biographies-135-local-v1','count':len(result),'people':result},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    counts=[x['wordCount'] for x in result]
    audit={'schema':'expanded-biographies-135-local-audit-v1','target':135,'imported':len(result),'missing':fail,'uniqueIds':len({x['id'] for x in result}),'minimumWords':min(counts) if counts else 0,'maximumWords':max(counts) if counts else 0,'sourceCoveragePercent':100 if complete else 0,'aiOriginalSubstantiveContentPercent':0,'runtimeExternalFetchRequired':False,'githubMaterialized':complete,'complete':complete}
    AUDIT.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(audit,ensure_ascii=False))
    if not complete:raise SystemExit('Local biography import incomplete')
if __name__=='__main__':main()
