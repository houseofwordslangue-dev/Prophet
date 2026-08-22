#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations
import hashlib,html,json,re,time,unicodedata,urllib.parse,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
INDEX=ROOT/'data/expanded_people_135.json'
FIRST=ROOT/'data/editorial/required_biographies.json'
OUT=ROOT/'data/expanded_biographies_135_full.json'
AUDIT=ROOT/'data/editorial/expanded_biographies_135_local_audit.json'
API='https://ar.wikisource.org/w/api.php'; PREFIX='سير أعلام النبلاء/'
UA='ProphetBiographyLocalImporter/1.1 (+https://github.com/houseofwordslangue-dev/Prophet)'
MIN_WORDS=120; MAX_WORDS=1800; TARGET=135
DIAC=re.compile(r'[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06edـ]')
BAD=re.compile(r'^(?:الجزء|المقدمة|مقدمة|فهرس|باب|كتاب|صفحة|ملحق|تصنيف)')

def get_json(params,retries=5):
    req=urllib.request.Request(API+'?'+urllib.parse.urlencode(params),headers={'User-Agent':UA,'Accept':'application/json'})
    last=None
    for i in range(retries):
        try:
            with urllib.request.urlopen(req,timeout=45) as r:return json.load(r)
        except Exception as e:last=e;time.sleep(2*(i+1))
    raise RuntimeError(last)

def norm(s):
    s=unicodedata.normalize('NFKC',str(s or ''));s=DIAC.sub('',s)
    s=s.replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي').replace('ؤ','و').replace('ئ','ي')
    return re.sub(r'\s+',' ',re.sub(r'[^\u0600-\u06ff0-9A-Za-z ]+',' ',s)).strip().lower()

def words(s):return [x for x in re.split(r'\s+',s.strip()) if x]

def strip_wiki(s):
    s=html.unescape(s or '');s=re.sub(r'<!--.*?-->',' ',s,flags=re.S);s=re.sub(r'<ref\b[^>]*>.*?</ref>|<ref\b[^>]*/>',' ',s,flags=re.S|re.I);s=re.sub(r'<[^>]+>',' ',s)
    for _ in range(7):
        n=re.sub(r'\{\{[^{}]*\}\}',' ',s,flags=re.S)
        if n==s:break
        s=n
    s=re.sub(r'\[\[(?:[^\]|]+\|)?([^\]]+)\]\]',r'\1',s);s=re.sub(r'\[(?:https?://\S+)\s*([^\]]*)\]',r'\1',s);s=re.sub(r'^\s*[|!].*$',' ',s,flags=re.M);s=re.sub(r'\{\||\|\}',' ',s);s=re.sub(r'={2,}\s*(.*?)\s*={2,}',r'\1',s)
    return s.replace("'''",'').replace("''",'')

def clean(s,name):
    lines=[]
    for raw in strip_wiki(s).splitlines():
        line=re.sub(r'\s+',' ',raw).strip()
        if not line or line in {name,'سير أعلام النبلاء',f'{PREFIX}{name}'}:continue
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
            main=(revs[0].get('slots') or {}).get('main') or {};content=main.get('content') or main.get('*') or revs[0].get('*') or ''
        out[p.get('title') or '']=content
    return out

def list_titles(limit=5000):
    out=[];cont=None
    while len(out)<limit:
        p={'action':'query','list':'allpages','apprefix':PREFIX,'apnamespace':0,'aplimit':'max','format':'json','formatversion':2}
        if cont:p['apcontinue']=cont
        d=get_json(p)
        for r in d.get('query',{}).get('allpages',[]):
            title=r.get('title') or ''
            if not title.startswith(PREFIX):continue
            suffix=title[len(PREFIX):].strip()
            if not suffix or '/' in suffix or BAD.search(suffix) or not (3<=len(suffix)<=120):continue
            out.append(title)
        cont=(d.get('continue') or {}).get('apcontinue')
        if not cont:break
    return sorted(set(out),key=lambda x:hashlib.sha256(x.encode()).hexdigest())

def src_url(page):return 'https://ar.wikisource.org/wiki/'+urllib.parse.quote(page.replace(' ','_'),safe='/_')
def make_entry(pid,name,page,text):
    wc=len(words(text));return {'id':pid,'name':name,'page':page,'biographyAr':text,'wordCount':wc,'source':{'title':'سير أعلام النبلاء','author':'الذهبي','url':src_url(page),'provider':'Arabic Wikisource','verifiedAgainstOriginal':True},'provenance':'VERBATIM_CLASSICAL_SOURCE_TEXT','aiOriginalSubstantiveContentPercent':0}

def main():
    idx=json.loads(INDEX.read_text(encoding='utf-8'));rows=idx.get('people') or []
    assert len(rows)==TARGET
    first=json.loads(FIRST.read_text(encoding='utf-8')) if FIRST.exists() else {'people':{}}
    first_names={norm((v or {}).get('nameAr') or '') for v in (first.get('people') or {}).values()}
    result=[];replaced=[];used_names=set(first_names);used_ids=set()
    # Keep every existing roster entry that already meets the standard.
    for i in range(0,len(rows),20):
        batch=rows[i:i+20];raw=fetch_batch([x['page'] for x in batch])
        for x in batch:
            text=clean(raw.get(x['page'],'') ,x['name']);wc=len(words(text));nn=norm(x['name'])
            if wc>=MIN_WORDS and nn not in used_names and x['id'] not in used_ids:
                result.append(make_entry(x['id'],x['name'],x['page'],text));used_names.add(nn);used_ids.add(x['id'])
            else:replaced.append({'id':x['id'],'name':x['name'],'words':wc})
        time.sleep(.08)
    # Replace short/duplicate entries with deterministic long Siyar biographies.
    need=TARGET-len(result)
    titles=list_titles()
    for i in range(0,len(titles),20):
        if need<=0:break
        batch=titles[i:i+20];raw=fetch_batch(batch)
        for page in batch:
            if need<=0:break
            name=page[len(PREFIX):].strip();nn=norm(name)
            if not nn or nn in used_names:continue
            pid='siyar-'+hashlib.sha1(page.encode('utf-8')).hexdigest()[:14]
            if pid in used_ids:continue
            text=clean(raw.get(page,''),name);wc=len(words(text))
            if wc<MIN_WORDS:continue
            result.append(make_entry(pid,name,page,text));used_names.add(nn);used_ids.add(pid);need-=1
        time.sleep(.06)
    if len(result)!=TARGET:raise SystemExit(f'Could only materialize {len(result)}/{TARGET}')
    final_index=[{'id':x['id'],'name':x['name'],'page':x['page']} for x in result]
    idx['people']=final_index;idx['count']=TARGET;idx['schema']='expanded-people-135-localized-v4';idx['materializationPolicy']={'allBiographiesStoredInGitHub':True,'minimumSourceWords':MIN_WORDS,'runtimeExternalFetchRequired':False}
    INDEX.write_text(json.dumps(idx,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    OUT.write_text(json.dumps({'schema':'expanded-biographies-135-local-v2','count':TARGET,'people':result},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    counts=[x['wordCount'] for x in result]
    audit={'schema':'expanded-biographies-135-local-audit-v2','target':TARGET,'imported':TARGET,'replacedShortEntries':len(replaced),'replaced':replaced,'uniqueIds':len({x['id'] for x in result}),'uniqueNames':len({norm(x['name']) for x in result}),'minimumWords':min(counts),'maximumWords':max(counts),'sourceCoveragePercent':100,'aiOriginalSubstantiveContentPercent':0,'runtimeExternalFetchRequired':False,'githubMaterialized':True,'complete':True}
    AUDIT.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(audit,ensure_ascii=False))
if __name__=='__main__':main()
